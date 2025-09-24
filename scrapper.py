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
import requests

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

# Initialize database
db = DatabaseManager()

# ----------------------- CONFIGURATION ---------------------------------
def get_api_base_url():
    """Get API base URL from environment or use dynamic detection"""
    # Try environment variable first
    api_url = os.getenv('LEGAL_API_URL')
    if api_url:
        return api_url
    
    # Try to detect the API server dynamically
    try:
        # Check if we're running locally
        import socket
        hostname = socket.gethostname()
        if hostname in ['localhost', '127.0.0.1']:
            return 'http://localhost:5002'
        
        # Try to get public IP
        response = requests.get('https://api.ipify.org', timeout=TIMEOUT_CONSTANTS['API_REQUEST_TIMEOUT'])
        if response.status_code == 200:
            public_ip = response.text.strip()
            return f'http://{public_ip}:5002'
    except Exception as e:
        print(f"Warning: Could not detect API URL dynamically: {e}")
    
    # Fallback to localhost
    return 'http://localhost:5002'

def get_file_paths():
    """Get file paths from environment or use defaults"""
    csv_folder = os.getenv('SCRAPER_CSV_FOLDER', '~/Desktop/scraped_cases')
    captcha_folder = os.getenv('SCRAPER_CAPTCHA_FOLDER', '~/Desktop/captcha_images')
    
    return Path(csv_folder).expanduser(), Path(captcha_folder).expanduser()

# Configuration constants
CNR_NUMBER = None                        # Will be set dynamically by scrape_case_details()
HEADLESS = os.getenv('SCRAPER_HEADLESS', 'True').lower() == 'true'
CSV_FOLDER, CAPTCHA_FOLDER = get_file_paths()
OCR_MODEL_NAME = os.getenv('OCR_MODEL_NAME', 'anuashok/ocr-captcha-v3')
PAGE_URL = "https://services.ecourts.gov.in/ecourtindia_v6/"
API_BASE_URL = get_api_base_url()

# Extraction constants
DEFAULT_VALUES = {
    'case_title': 'Unknown',
    'petitioner': 'Unknown',
    'respondent': 'Unknown',
    'case_type': 'Civil',
    'court_name': 'Unknown Court',
    'judge_name': 'Unknown Judge',
    'status': 'Active',
    'registration_number': 'Unknown'
}

EXTRACTION_CONSTANTS = {
    'MIN_TEXT_LENGTH': 10,
    'MIN_CELLS_FOR_EXTRACTION': 4,
    'MIN_CELLS_FOR_HISTORY': 4
}

COURT_PATTERNS = {
    'High Court': 'High Court',
    'Supreme Court': 'Supreme Court',
    'District Court': 'District Court',
    'Family Court': 'Family Court',
    'Sessions Court': 'Sessions Court',
    'Magistrate Court': 'Magistrate Court'
}

# Timeout constants
TIMEOUT_CONSTANTS = {
    'API_REQUEST_TIMEOUT': int(os.getenv('API_REQUEST_TIMEOUT', '5')),
    'DRIVER_WAIT_TIMEOUT': int(os.getenv('DRIVER_WAIT_TIMEOUT', '30')),
    'THREAD_JOIN_TIMEOUT': int(os.getenv('THREAD_JOIN_TIMEOUT', '20'))
}
# ------------------------------------------------------------------------

# Cache settings
USE_CACHE_IF_FAIL = True   # Enable cache fallback for better reliability
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
        # try:
        #     send_log_to_api("Testing Chrome driver with simple page load...", 'info', 'scraper')
        #     driver.get("data:text/html,<html><body><h1>Test</h1></body></html>")
        #     send_log_to_api("Chrome driver test successful", 'success', 'scraper')
        # except Exception as e:
        #     send_log_to_api(f"Chrome driver test failed: {str(e)}", 'error', 'scraper')
        #     raise e
        
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
    # Validate CNR number
    if not cnr_number or not isinstance(cnr_number, str) or len(cnr_number.strip()) == 0:
        return {
            'success': False,
            'error': 'CNR number is required and must be a non-empty string',
            'extracted_real_data': False
        }
    
    # Update the global CNR_NUMBER
    global CNR_NUMBER
    CNR_NUMBER = cnr_number.strip()
    
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
            t.join(timeout=TIMEOUT_CONSTANTS['DRIVER_WAIT_TIMEOUT'])  # Use configurable timeout
            if t.is_alive():
                print(f"Page did not load within {TIMEOUT_CONSTANTS['DRIVER_WAIT_TIMEOUT']} seconds. Loading from cache...")
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


def sanitize_text(text):
    """Sanitize and clean extracted text"""
    if not text or text == 'Unknown':
        return DEFAULT_VALUES.get('case_title', 'Unknown')
    
    # Remove extra whitespace and normalize
    text = ' '.join(text.split())
    
    # Remove common unwanted characters
    unwanted_chars = ['\n', '\r', '\t', '\xa0']
    for char in unwanted_chars:
        text = text.replace(char, ' ')
    
    # Remove extra spaces again
    text = ' '.join(text.split())
    
    return text.strip() if text.strip() else 'Unknown'

def validate_date(date_str):
    """Validate and format date string"""
    if not date_str or date_str == 'Unknown':
        return None
    
    try:
        # Try common date formats
        date_formats = ['%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d']
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # If no format matches, return as-is
        return date_str
    except Exception:
        return None

def extract_court_name(judge_text):
    """Extract court name from judge text with improved logic"""
    if not judge_text or judge_text == 'Unknown':
        return DEFAULT_VALUES['court_name']
    
    # Split by common separators
    separators = [' - ', ' vs ', ' | ', ' / ']
    for sep in separators:
        if sep in judge_text:
            parts = judge_text.split(sep)
            if len(parts) >= 2:
                potential_court = parts[1].strip()
                if len(potential_court) > 5:  # Reasonable court name length
                    return potential_court
    
    # Look for court patterns
    for pattern, court_name in COURT_PATTERNS.items():
        if pattern in judge_text:
            return court_name
    
    # Check for state-specific courts
    if 'Karnataka' in judge_text:
        return 'High Court of Karnataka'
    elif 'Supreme' in judge_text:
        return 'Supreme Court of India'
    
    return DEFAULT_VALUES['court_name']

def extract_case_type_from_text(all_text, case_title):
    """Extract case type from text content with improved logic"""
    if not all_text:
        return DEFAULT_VALUES['case_type']
    
    text_lower = all_text.lower()
    
    # Use case title if available and meaningful
    if case_title and case_title != 'Unknown' and len(case_title) > 5:
        return case_title
    
    # Look for specific case type patterns
    if 'matrimonial' in text_lower and 'case' in text_lower:
        return 'Matrimonial Case'
    elif 'criminal' in text_lower and 'case' in text_lower:
        return 'Criminal Case'
    elif 'civil' in text_lower and 'case' in text_lower:
        return 'Civil Case'
    elif 'family' in text_lower and 'case' in text_lower:
        return 'Family Case'
    elif 'property' in text_lower and 'case' in text_lower:
        return 'Property Case'
    elif 'divorce' in text_lower:
        return 'Divorce Case'
    elif 'maintenance' in text_lower:
        return 'Maintenance Case'
    
    return DEFAULT_VALUES['case_type']

def validate_extracted_data(case_data):
    """Validate and clean extracted case data"""
    validated_data = {}
    
    # Sanitize text fields
    text_fields = ['case_title', 'petitioner', 'respondent', 'judge_name', 'court_name', 'case_type', 'status', 'registration_number']
    for field in text_fields:
        validated_data[field] = sanitize_text(case_data.get(field, DEFAULT_VALUES[field]))
    
    # Validate date
    validated_data['filing_date'] = validate_date(case_data.get('filing_date'))
    
    return validated_data

def extract_case_details(driver):
    """Extract case details from the results page with improved validation and logging"""
    send_log_to_api("Starting case details extraction", 'info', 'scraper')
    
    # Initialize with default values
    case_data = DEFAULT_VALUES.copy()
    case_data['filing_date'] = None
    
    try:
        # Get the page source for debugging
        page_source = driver.page_source
        
        # Approach 1: Extract from case history table
        try:
            send_log_to_api("Attempting history table extraction", 'info', 'scraper')
            history_table = driver.find_element(By.CLASS_NAME, "history_table")
            rows = history_table.find_elements(By.TAG_NAME, "tr")
            
            for row in rows[1:]:  # Skip header row
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= EXTRACTION_CONSTANTS['MIN_CELLS_FOR_HISTORY']:
                    judge_text = cells[0].text.strip()
                    business_date = cells[1].text.strip()
                    hearing_date = cells[2].text.strip()
                    
                    # Extract court name and judge using improved function
                    if judge_text and judge_text != '':
                        case_data['judge_name'] = sanitize_text(judge_text.split(' - ')[0] if ' - ' in judge_text else judge_text)
                        case_data['court_name'] = extract_court_name(judge_text)
                    
                    # Extract filing date with validation
                    if business_date and business_date != '' and case_data['filing_date'] is None:
                        case_data['filing_date'] = validate_date(business_date)
                    elif hearing_date and hearing_date != '' and case_data['filing_date'] is None:
                        case_data['filing_date'] = validate_date(hearing_date)
                    
                    # Break after first row since we have the main info
                    break
            
            send_log_to_api(f"History table extraction completed: court={case_data['court_name']}, judge={case_data['judge_name']}", 'info', 'scraper')
        except Exception as e:
            send_log_to_api(f"Error extracting from history table: {e}", 'warning', 'scraper')
        
        # Approach 2: Look for table rows with case information
        try:
            send_log_to_api("Attempting table row extraction", 'info', 'scraper')
            tables = driver.find_elements(By.TAG_NAME, "table")
            for table in tables:
                rows = table.find_elements(By.TAG_NAME, "tr")
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 2:
                        cell_text = cells[0].text.strip().lower()
                        cell_value = cells[1].text.strip()
                        
                        if 'case title' in cell_text and cell_value:
                            case_data['case_title'] = sanitize_text(cell_value)
                        elif 'petitioner' in cell_text and cell_value:
                            case_data['petitioner'] = sanitize_text(cell_value)
                        elif 'respondent' in cell_text and cell_value:
                            case_data['respondent'] = sanitize_text(cell_value)
                        elif 'case type' in cell_text and cell_value:
                            case_data['case_type'] = sanitize_text(cell_value)
                        elif 'court' in cell_text and cell_value and case_data['court_name'] == DEFAULT_VALUES['court_name']:
                            case_data['court_name'] = sanitize_text(cell_value)
                        elif 'judge' in cell_text and cell_value and case_data['judge_name'] == DEFAULT_VALUES['judge_name']:
                            case_data['judge_name'] = sanitize_text(cell_value)
                        elif 'filing date' in cell_text and cell_value:
                            case_data['filing_date'] = validate_date(cell_value)
                        elif 'registration' in cell_text and cell_value:
                            case_data['registration_number'] = sanitize_text(cell_value)
            
            send_log_to_api(f"Table extraction completed: title={case_data['case_title']}, petitioner={case_data['petitioner']}", 'info', 'scraper')
        except Exception as e:
            send_log_to_api(f"Error in table extraction: {e}", 'warning', 'scraper')
        
        # Approach 3: Look for case title in headings
        try:
            send_log_to_api("Attempting heading extraction", 'info', 'scraper')
            headings = driver.find_elements(By.TAG_NAME, "h1")
            headings.extend(driver.find_elements(By.TAG_NAME, "h2"))
            headings.extend(driver.find_elements(By.TAG_NAME, "h3"))
            
            for heading in headings:
                text = heading.text.strip()
                if text and len(text) > EXTRACTION_CONSTANTS['MIN_TEXT_LENGTH'] and 'case' in text.lower():
                    case_data['case_title'] = sanitize_text(text)
                    break
            
            send_log_to_api(f"Heading extraction completed: title={case_data['case_title']}", 'info', 'scraper')
        except Exception as e:
            send_log_to_api(f"Error in heading extraction: {e}", 'warning', 'scraper')
        
        # Approach 4: Extract case type from text content with improved logic
        try:
            send_log_to_api("Attempting case type extraction from text", 'info', 'scraper')
            all_text = driver.find_element(By.TAG_NAME, "body").text
            case_data['case_type'] = extract_case_type_from_text(all_text, case_data['case_title'])
            send_log_to_api(f"Case type extraction completed: type={case_data['case_type']}", 'info', 'scraper')
        except Exception as e:
            send_log_to_api(f"Error in case type extraction: {e}", 'warning', 'scraper')
        
        # Approach 5: Generate fallback case title if needed
        if case_data['case_title'] == DEFAULT_VALUES['case_title']:
            if case_data['petitioner'] != DEFAULT_VALUES['petitioner']:
                case_data['case_title'] = f"{case_data['petitioner']} vs {case_data['respondent'] if case_data['respondent'] != DEFAULT_VALUES['respondent'] else 'State'}"
            else:
                case_data['case_title'] = f"Case - {CNR_NUMBER}"
        
        # Validate and clean all extracted data
        send_log_to_api("Validating extracted data", 'info', 'scraper')
        case_data = validate_extracted_data(case_data)
        
        send_log_to_api(f"Case details extraction completed successfully: {case_data}", 'success', 'scraper')
        
    except Exception as e:
        send_log_to_api(f"Critical error in case details extraction: {e}", 'error', 'scraper')
        # Return default data on critical error
        case_data = DEFAULT_VALUES.copy()
        case_data['filing_date'] = None
    
    return case_data


def send_log_to_api(message, log_type='info', source='scraper'):
    """Send log message to API server using dynamic URL detection"""
    try:
        # Use the dynamically configured API base URL
        log_url = f"{API_BASE_URL}/api/logs/add"
        
        # Try the configured URL first
        try:
            response = requests.post(log_url, 
                                   json={'message': message, 'type': log_type, 'source': source},
                                   timeout=TIMEOUT_CONSTANTS['API_REQUEST_TIMEOUT'])
            if response.status_code == 200:
                return
        except Exception as e:
            print(f"Failed to send log to {log_url}: {e}")
        
        # Fallback URLs (only if main URL fails)
        fallback_urls = [
            'http://localhost:5002/api/logs/add',
            'http://127.0.0.1:5002/api/logs/add'
        ]
        
        for url in fallback_urls:
            try:
                response = requests.post(url, 
                                       json={'message': message, 'type': log_type, 'source': source},
                                       timeout=TIMEOUT_CONSTANTS['API_REQUEST_TIMEOUT'])
                if response.status_code == 200:
                    return
            except Exception as e:
                print(f"Failed to send log to {url}: {e}")
                continue
        
        print(f"All log endpoints failed for message: {message}")
        
    except Exception as e:
        print(f"Error in send_log_to_api: {e}")


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
            t.join(timeout=TIMEOUT_CONSTANTS['THREAD_JOIN_TIMEOUT'])
            if t.is_alive():
                print(f"Page did not load within {TIMEOUT_CONSTANTS['THREAD_JOIN_TIMEOUT']} seconds. Loading from cache...")
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

