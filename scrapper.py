"""
e-Courts CNR Scraper (Optimized for Speed)
----------------------------------------------------------
• Opens https://services.ecourts.gov.in/ecourtindia_v6/
• Enters a CNR, captures the CAPTCHA image
• Uses TrOCR (anuashok/ocr-captcha-v3) to read the CAPTCHA
• Submits the form and downloads the case-history table
• Saves the table to ~/Desktop/shantharam/case_history_<CNR>_<timestamp>.csv
----------------------------------------------------------
Requires:
pip install selenium==4.20.0 pillow transformers torch torchvision
• Chrome 127+ and matching chromedriver on PATH
"""

import os, sys, csv, time
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from PIL import Image
import torch
from transformers import VisionEncoderDecoderModel, TrOCRProcessor
from database_setup import DatabaseManager
import requests

# Initialize database
db = DatabaseManager()

# ----------------------- CONFIG ---------------------------------
CNR_NUMBER = "KAUP050003552024"          # <-- change as required
HEADLESS = True                          # Set to True for EC2/headless servers
CSV_FOLDER = Path("~/Desktop/shantharam").expanduser()
CAPTCHA_FOLDER = Path("~/Desktop/captcha_images").expanduser()
OCR_MODEL_NAME = "anuashok/ocr-captcha-v3"
PAGE_URL = "https://services.ecourts.gov.in/ecourtindia_v6/"
# ----------------------------------------------------------------

# Cache settings
USE_CACHE_IF_FAIL = False  # Disabled cache to force real website loading
CACHE_FILE = Path("ecourts_homepage.html")


def create_driver(headless: bool = True) -> webdriver.Chrome:
    try:
        send_log_to_api("Creating Chrome driver...", 'info', 'scraper')
        
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        
        # Essential options for stability (CRITICAL for EC2)
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Additional EC2/headless server options
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")  # Speed up loading
        # chrome_options.add_argument("--disable-javascript")  # Commented out - needed for e-courts
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-features=TranslateUI")
        chrome_options.add_argument("--disable-ipc-flooding-protection")
        chrome_options.add_argument("--single-process")  # Use single process for stability
        chrome_options.add_argument("--disable-web-security")  # If needed for CORS
        chrome_options.add_argument("--remote-debugging-port=9222")  # For debugging
        
        # Window size and position
        chrome_options.add_argument("--window-size=1920,1080")
        # Remove --start-maximized for headless mode
        if not headless:
            chrome_options.add_argument("--start-maximized")
        
        # Mimic real browser to avoid throttling
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36")
        
        # Add experimental options
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        service = Service()  # Assumes chromedriver on PATH
        
        send_log_to_api("Initializing Chrome driver...", 'info', 'scraper')
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Execute script to remove webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        send_log_to_api("Chrome driver created successfully", 'success', 'scraper')
        
        # Test if driver is working
        try:
            send_log_to_api("Testing Chrome driver with simple page load...", 'info', 'scraper')
            driver.get("data:text/html,<html><body><h1>Test</h1></body></html>")
            send_log_to_api("Chrome driver test successful", 'success', 'scraper')
        except Exception as e:
            send_log_to_api(f"Chrome driver test failed: {str(e)}", 'error', 'scraper')
            raise e
        
        return driver
        
    except Exception as e:
        error_msg = f"Failed to create Chrome driver: {str(e)}"
        send_log_to_api(error_msg, 'error', 'scraper')
        raise Exception(error_msg)


def save_captcha(driver) -> Path:
    CAPTCHA_FOLDER.mkdir(parents=True, exist_ok=True)
    wait = WebDriverWait(driver, 10)
    captcha_img = wait.until(EC.presence_of_element_located((By.ID, "captcha_image")))

    filename = f"captcha_{datetime.now():%Y%m%d_%H%M%S}.png"
    filepath = CAPTCHA_FOLDER / filename
    captcha_img.screenshot(str(filepath))
    return filepath


def solve_captcha(img_path: Path, processor, model) -> str:
    image = Image.open(img_path).convert("RGBA")
    bg = Image.new("RGBA", image.size, (255, 255, 255))
    image = Image.alpha_composite(bg, image).convert("RGB")

    with torch.no_grad():
        pixel_vals = processor(image, return_tensors="pt").pixel_values
        ids = model.generate(pixel_vals)
        txt = processor.batch_decode(ids, skip_special_tokens=True)[0]
    return txt.strip()


# API FUNCTION: scrape_case_details(cnr_number) - Called by Flask API, no database insertion - LINE 125
def scrape_case_details(cnr_number):
    """
    Scrape case details from eCourts for a given CNR number
    Returns a dictionary with case information (NO DATABASE INSERTION)
    This function is called by the API and does NOT insert into database
    """
    # Update the global CNR_NUMBER
    global CNR_NUMBER
    CNR_NUMBER = cnr_number
    
    start_time = time.perf_counter()
    CSV_FOLDER.mkdir(parents=True, exist_ok=True)

    print("Loading TrOCR model …")
    model_start = time.perf_counter()
    processor = TrOCRProcessor.from_pretrained(OCR_MODEL_NAME)
    model = VisionEncoderDecoderModel.from_pretrained(OCR_MODEL_NAME)
    print(f"Model loaded in {time.perf_counter() - model_start:.2f}s")

    driver = create_driver(HEADLESS)
    try:
        get_start = time.perf_counter()
        try:
            import threading
            exc = {}
            def load_page():
                try:
                    driver.get(PAGE_URL)
                except Exception as e:
                    exc['error'] = e
            t = threading.Thread(target=load_page)
            t.start()
            t.join(timeout=30)  # Increased timeout to 30 seconds
            if t.is_alive():
                print("Page did not load within 30 seconds. Loading from cache...")
                # Optionally, try to stop the thread/browser here
                if USE_CACHE_IF_FAIL and CACHE_FILE.exists():
                    with CACHE_FILE.open("r", encoding="utf-8") as f:
                        html = f.read()
                    driver.get("data:text/html;charset=utf-8," + html)
                else:
                    raise TimeoutException("Page did not load in 30 seconds and no cache available.")
            elif 'error' in exc:
                print(f"Error loading live page: {exc['error']}")
                if USE_CACHE_IF_FAIL and CACHE_FILE.exists():
                    print("Loading page from cache...")
                    with CACHE_FILE.open("r", encoding="utf-8") as f:
                        html = f.read()
                    driver.get("data:text/html;charset=utf-8," + html)
                else:
                    raise exc['error']
            else:
                print(f"Page loaded in {time.perf_counter() - get_start:.2f}s")
                # Save page source to cache
                with CACHE_FILE.open("w", encoding="utf-8") as f:
                    f.write(driver.page_source)
        except Exception as e:
            print(f"Error loading live page: {e}")
            if USE_CACHE_IF_FAIL and CACHE_FILE.exists():
                print("Loading page from cache...")
                with CACHE_FILE.open("r", encoding="utf-8") as f:
                    html = f.read()
                driver.get("data:text/html;charset=utf-8," + html)
            else:
                raise

        time.sleep(1)  # Stability pause

        # Retry loop for CNR field (fixes flaky timeouts)
        quick_wait = WebDriverWait(driver, 15)
        for cnr_attempt in range(3):  # Try up to 3 times
            try:
                cnr_box = quick_wait.until(EC.visibility_of_element_located((By.ID, "cino")))
                cnr_box.clear()
                cnr_box.send_keys(CNR_NUMBER)
                print("Entered CNR:", CNR_NUMBER)
                break
            except TimeoutException:
                print(f"Timeout on CNR attempt {cnr_attempt+1}/3 - retrying...")
                time.sleep(2)
        else:
            print("CNR field not found after retries. Dumping page source for debugging:")
            print(driver.page_source[:2000])
            raise TimeoutException("CNR field not found after retries")

        img_path = save_captcha(driver)
        print("Saved CAPTCHA:", img_path)
        captcha_text = solve_captcha(img_path, processor, model)
        print("OCR decoded CAPTCHA:", captcha_text)

        cap_box = driver.find_element(By.ID, "fcaptcha_code")
        cap_box.clear()
        cap_box.send_keys(captcha_text)
        driver.find_element(By.ID, "searchbtn").click()

        hist_wait = WebDriverWait(driver, 15)
        hist_wait.until(EC.presence_of_element_located((By.CLASS_NAME, "history_table")))

        rows = driver.find_elements(By.CSS_SELECTOR, ".history_table tr")[1:]
        history = []
        for r in rows:
            cells = r.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 4:
                # Extract all available columns including Status
                judge = cells[0].text.strip() if len(cells) > 0 else ""
                business_date = cells[1].text.strip() if len(cells) > 1 else ""
                hearing_date = cells[2].text.strip() if len(cells) > 2 else ""
                purpose = cells[3].text.strip() if len(cells) > 3 else ""
                status = cells[4].text.strip() if len(cells) > 4 else ""  # 5th column for Status
                
                print(f"🔍 Found {len(cells)} columns: Judge='{judge}', Business='{business_date}', Hearing='{hearing_date}', Purpose='{purpose}', Status='{status}'")
                
                history.append({
                    "Judge": judge,
                    "Business_on_Date": business_date,
                    "Hearing_Date": hearing_date,
                    "Purpose_of_Hearing": purpose,
                    "Status": status,
                })

        if not history:
            print("No history found — CAPTCHA may be wrong or case has no data.")
            raise Exception("No history found — CAPTCHA may be wrong or case has no data.")

        # Extract case details from the page
        case_data = extract_case_details(driver)
        print(f"🔍 Extracted case data: {case_data}")
        
        # Check if we actually extracted meaningful data
        extracted_real_data = (
            case_data.get('case_type') != 'Civil' and
            case_data.get('case_type') != 'Unknown' and
            case_data.get('court_name') != 'Unknown Court' and
            case_data.get('judge_name') != 'Unknown Judge'
        )
        
        print(f"🔍 Data extraction quality: {'✅ Real data found' if extracted_real_data else '⚠️ Default values detected'}")
        send_log_to_api(f"Scraping completed successfully! Found {len(history)} history records.", 'success', 'scraper')
        print(f"✅ Scraping completed successfully! Found {len(history)} history records.")
        print(f"Total runtime: {time.perf_counter() - start_time:.2f}s")

        # Return the scraped data (NO DATABASE INSERTION) - scrape_case_details function
        return {
            'success': True,
            'cnr_number': CNR_NUMBER,
            'case_title': case_data.get('case_title', 'N/A'),
            'petitioner': case_data.get('petitioner', 'N/A'),
            'respondent': case_data.get('respondent', 'N/A'),
            'case_type': case_data.get('case_type', 'N/A'),
            'court_name': case_data.get('court_name', 'N/A'),
            'judge_name': case_data.get('judge_name', 'N/A'),
            'status': case_data.get('status', 'N/A'),
            'filing_date': case_data.get('filing_date'),
            'registration_number': case_data.get('registration_number'),
            'case_history': history,  # Include full history data
            'case_history_count': len(history),
            'extracted_real_data': extracted_real_data
        }
        
    except Exception as e:
        print(f"Error: {e}")
        send_log_to_api(f"Scraping failed: {str(e)}", 'error', 'scraper')
        return {'success': False, 'error': str(e)}

    finally:
        driver.quit()


def extract_case_details(driver):
    """Extract case details from the results page"""
    case_data = {
        'case_title': 'Unknown',
        'petitioner': 'Unknown',
        'respondent': 'Unknown',
        'case_type': 'Civil',
        'court_name': 'Unknown Court',
        'judge_name': 'Unknown Judge',
        'status': 'Active',
        'filing_date': None,
        'registration_number': 'Unknown'
    }
    
    try:
        # Get the page source for debugging
        page_source = driver.page_source
        
        # First, try to extract court name from case history table
        try:
            history_table = driver.find_element(By.CLASS_NAME, "history_table")
            rows = history_table.find_elements(By.TAG_NAME, "tr")
            
            for row in rows[1:]:  # Skip header row
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 4:
                    judge_text = cells[0].text.strip()
                    business_date = cells[1].text.strip()
                    hearing_date = cells[2].text.strip()
                    
                    # Extract court name and judge from judge column
                    if judge_text and judge_text != '':
                        # Extract court name from judge text
                        # Judge text usually contains: "Judge Name - Court Name"
                        if ' - ' in judge_text:
                            parts = judge_text.split(' - ')
                            if len(parts) >= 2:
                                case_data['judge_name'] = parts[0].strip()
                                case_data['court_name'] = parts[1].strip()
                        elif 'High Court' in judge_text or 'Supreme Court' in judge_text:
                            case_data['judge_name'] = judge_text
                            if 'Karnataka' in judge_text:
                                case_data['court_name'] = 'High Court of Karnataka'
                            elif 'Supreme' in judge_text:
                                case_data['court_name'] = 'Supreme Court of India'
                    
                    # Extract filing date from business date or hearing date
                    if business_date and business_date != '' and case_data['filing_date'] is None:
                        try:
                            # Try to parse the business date as filing date
                            case_data['filing_date'] = business_date
                        except:
                            pass
                    elif hearing_date and hearing_date != '' and case_data['filing_date'] is None:
                        try:
                            # Try to parse the hearing date as filing date
                            case_data['filing_date'] = hearing_date
                        except:
                            pass
                    
                    # Break after first row since we have the main info
                    break
        except Exception as e:
            print(f"Error extracting from history table: {e}")
        
        # Try multiple approaches to extract other case details
        
        # Approach 1: Look for table rows with case information
        try:
            # Look for any table that might contain case details
            tables = driver.find_elements(By.TAG_NAME, "table")
            for table in tables:
                rows = table.find_elements(By.TAG_NAME, "tr")
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 2:
                        cell_text = cells[0].text.strip().lower()
                        cell_value = cells[1].text.strip()
                        
                        if 'case title' in cell_text and cell_value:
                            case_data['case_title'] = cell_value
                        elif 'petitioner' in cell_text and cell_value:
                            case_data['petitioner'] = cell_value
                        elif 'respondent' in cell_text and cell_value:
                            case_data['respondent'] = cell_value
                        elif 'case type' in cell_text and cell_value:
                            case_data['case_type'] = cell_value
                        elif 'court' in cell_text and cell_value and case_data['court_name'] == 'Unknown Court':
                            case_data['court_name'] = cell_value
                        elif 'judge' in cell_text and cell_value and case_data['judge_name'] == 'Unknown Judge':
                            case_data['judge_name'] = cell_value
                        elif 'filing date' in cell_text and cell_value:
                            case_data['filing_date'] = cell_value
                        elif 'registration' in cell_text and cell_value:
                            case_data['registration_number'] = cell_value
        except Exception as e:
            print(f"Error in table extraction: {e}")
        
        # Approach 2: Look for specific text patterns
        try:
            # Look for case title in headings or strong text
            headings = driver.find_elements(By.TAG_NAME, "h1")
            headings.extend(driver.find_elements(By.TAG_NAME, "h2"))
            headings.extend(driver.find_elements(By.TAG_NAME, "h3"))
            
            for heading in headings:
                text = heading.text.strip()
                if text and len(text) > 10 and 'case' in text.lower():
                    case_data['case_title'] = text
                    break
        except Exception as e:
            print(f"Error in heading extraction: {e}")
        
        # Approach 3: Look for specific text patterns (conservative approach)
        try:
            # Only extract if we haven't found anything better
            if case_data['case_type'] == 'Civil' and case_data['court_name'] == 'Unknown Court':
                all_text = driver.find_element(By.TAG_NAME, "body").text
                
                # Only set if we find very specific patterns
                if 'matrimonial' in all_text.lower() and 'case' in all_text.lower():
                    # Use case title instead of hardcoded case type
                    if case_data['case_title'] != 'Unknown':
                        case_data['case_type'] = case_data['case_title']
                    else:
                        case_data['case_type'] = 'M.C. - MATRIMONIAL CASES'
                elif 'criminal' in all_text.lower() and 'case' in all_text.lower():
                    # Use case title instead of hardcoded case type
                    if case_data['case_title'] != 'Unknown':
                        case_data['case_type'] = case_data['case_title']
                    else:
                        case_data['case_type'] = 'Criminal'
                # Keep 'Civil' as default if no specific pattern found
            
        except Exception as e:
            print(f"Error in text pattern extraction: {e}")
        
        # If we still don't have a proper case title, try to create one from available data
        if case_data['case_title'] == 'Unknown':
            if case_data['petitioner'] != 'Unknown':
                case_data['case_title'] = f"{case_data['petitioner']} vs {case_data['respondent'] if case_data['respondent'] != 'Unknown' else 'State'}"
            else:
                case_data['case_title'] = f"Case - {CNR_NUMBER}"
        
        print(f"Extracted case details: {case_data}")
        
    except Exception as e:
        print(f"Error extracting case details: {e}")
    
    return case_data


def send_log_to_api(message, log_type='info', source='scraper'):
    """Send log message to API server"""
    try:
        # Try localhost first, then fallback to the original IP
        urls_to_try = [
            'http://localhost:5002/api/logs/add',
            'http://127.0.0.1:5002/api/logs/add',
            'http://52.23.206.51:5002/api/logs/add'
        ]
        
        for url in urls_to_try:
            try:
                requests.post(url, 
                             json={'message': message, 'type': log_type, 'source': source},
                             timeout=1)
                break  # If successful, stop trying other URLs
            except:
                continue  # Try next URL
    except:
        # Silently fail if API is not available
        pass


def main():
    start_time = time.perf_counter()
    CSV_FOLDER.mkdir(parents=True, exist_ok=True)

    print("Loading TrOCR model …")
    model_start = time.perf_counter()
    processor = TrOCRProcessor.from_pretrained(OCR_MODEL_NAME)
    model = VisionEncoderDecoderModel.from_pretrained(OCR_MODEL_NAME)
    print(f"Model loaded in {time.perf_counter() - model_start:.2f}s")

    driver = create_driver(HEADLESS)
    try:
        get_start = time.perf_counter()
        try:
            import threading
            exc = {}
            def load_page():
                try:
                    driver.get(PAGE_URL)
                except Exception as e:
                    exc['error'] = e
            t = threading.Thread(target=load_page)
            t.start()
            t.join(timeout=20)
            if t.is_alive():
                print("Page did not load within 5 seconds. Loading from cache...")
                # Optionally, try to stop the thread/browser here
                if USE_CACHE_IF_FAIL and CACHE_FILE.exists():
                    with CACHE_FILE.open("r", encoding="utf-8") as f:
                        html = f.read()
                    driver.get("data:text/html;charset=utf-8," + html)
                else:
                    raise TimeoutException("Page did not load in 5 seconds and no cache available.")
            elif 'error' in exc:
                print(f"Error loading live page: {exc['error']}")
                if USE_CACHE_IF_FAIL and CACHE_FILE.exists():
                    print("Loading page from cache...")
                    with CACHE_FILE.open("r", encoding="utf-8") as f:
                        html = f.read()
                    driver.get("data:text/html;charset=utf-8," + html)
                else:
                    raise exc['error']
            else:
                print(f"Page loaded in {time.perf_counter() - get_start:.2f}s")
                # Save page source to cache
                with CACHE_FILE.open("w", encoding="utf-8") as f:
                    f.write(driver.page_source)
        except Exception as e:
            print(f"Error loading live page: {e}")
            if USE_CACHE_IF_FAIL and CACHE_FILE.exists():
                print("Loading page from cache...")
                with CACHE_FILE.open("r", encoding="utf-8") as f:
                    html = f.read()
                driver.get("data:text/html;charset=utf-8," + html)
            else:
                raise

        time.sleep(1)  # Stability pause

        # Retry loop for CNR field (fixes flaky timeouts)
        quick_wait = WebDriverWait(driver, 15)
        for attempt in range(3):  # Try up to 3 times
            try:
                cnr_box = quick_wait.until(EC.visibility_of_element_located((By.ID, "cino")))
                cnr_box.clear()
                cnr_box.send_keys(CNR_NUMBER)
                print("Entered CNR:", CNR_NUMBER)
                break
            except TimeoutException:
                print(f"Timeout on attempt {attempt+1}/3 - retrying...")
                time.sleep(2)
            else:
                print("CNR field not found after retries. Dumping page source for debugging:")
                print(driver.page_source[:2000])
                raise TimeoutException("CNR field not found after retries")

        img_path = save_captcha(driver)
        print("Saved CAPTCHA:", img_path)
        captcha_text = solve_captcha(img_path, processor, model)
        print("OCR decoded CAPTCHA:", captcha_text)

        cap_box = driver.find_element(By.ID, "fcaptcha_code")
        cap_box.clear()
        cap_box.send_keys(captcha_text)
        driver.find_element(By.ID, "searchbtn").click()

        hist_wait = WebDriverWait(driver, 15)
        hist_wait.until(EC.presence_of_element_located((By.CLASS_NAME, "history_table")))

        rows = driver.find_elements(By.CSS_SELECTOR, ".history_table tr")[1:]
        history = []
        for r in rows:
            cells = r.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 4:
                history.append(
                    {
                        "Judge": cells[0].text.strip(),
                        "Business_on_Date": cells[1].text.strip(),
                        "Hearing_Date": cells[2].text.strip(),
                        "Purpose_of_Hearing": cells[3].text.strip(),
                    }
                )

        if not history:
            print("No history found — CAPTCHA may be wrong or case has no data.")
            raise Exception("No history found — CAPTCHA may be wrong or case has no data.")

        # Insert case (fill in actual scraped values if available)
        case_success = db.insert_case(
            CNR_NUMBER,
            case_title="N/A",  # Replace with actual value if scraped
            petitioner="N/A",
            respondent="N/A",
            case_type="N/A",
            court_name="N/A",
            judge_name="N/A",
            status="N/A",
            filing_date=None,
            case_description=None,
            registration_number=None
        )
        
        if not case_success:
            raise Exception(f"Failed to insert case for CNR {CNR_NUMBER}")

        # Insert case history
        history_success_count = 0
        for row in history:
            print(f"🔍 Inserting history row: Judge='{row['Judge']}', Business_Date='{row['Business_on_Date']}', Hearing_Date='{row['Hearing_Date']}', Purpose='{row['Purpose_of_Hearing']}'")
            success = db.insert_case_history(
                CNR_NUMBER,
                row["Judge"],
                row["Business_on_Date"],
                row["Hearing_Date"],
                row["Purpose_of_Hearing"]
            )
            if success:
                history_success_count += 1
            else:
                print(f"Warning: Failed to insert case history row for CNR {CNR_NUMBER}")
        
        if history_success_count == 0 and len(history) > 0:
            raise Exception(f"Failed to insert any case history for CNR {CNR_NUMBER}")

        print(f"✅  Saved {history_success_count} rows to the database for CNR {CNR_NUMBER}")
        print(f"Total runtime: {time.perf_counter() - start_time:.2f}s")

    except Exception as e:
        print(f"Error: {e}")
        print("Page source snippet:\n", driver.page_source[:500])
        raise  # Re-raise the exception so the retry loop catches it

    finally:
        driver.quit()


if __name__ == "__main__":
    import os
    import sys
    import time

    MAX_RETRIES = 3
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"\n--- Scraper attempt {attempt} of {MAX_RETRIES} ---")
            # Use scrape_case_details instead of main() for consistency
            result = scrape_case_details(CNR_NUMBER)
            if result and result.get('success'):
                if result.get('extracted_real_data', False):
                    print("✅ Scraping completed successfully with real data!")
                    break  # Success, exit loop
                else:
                    print("⚠️ Scraping completed but only default data found - retrying...")
                    raise Exception("Only default data extracted - retrying for better results")
            else:
                raise Exception("Scraping returned failure")
        except Exception as e:
            print(f"❌ Scraper failed on attempt {attempt}: {e}")
            if attempt < MAX_RETRIES:
                print("Retrying in 5 seconds...")
                time.sleep(5)
            else:
                print("❌ All attempts failed. Restarting script as a new process.")
                python = sys.executable
                os.execv(python, [python] + sys.argv)
