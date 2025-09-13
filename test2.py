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

# ----------------------- CONFIG ---------------------------------
CNR_NUMBER      = "KAUP050003552024"          # <-- change as required
HEADLESS        = False                       # Set to False for faster loading (mimics normal browser)
CSV_FOLDER      = Path("~/Desktop/shantharam").expanduser()
CAPTCHA_FOLDER  = Path("~/Desktop/captcha_images").expanduser()
OCR_MODEL_NAME  = "anuashok/ocr-captcha-v3"
PAGE_URL        = "https://services.ecourts.gov.in/ecourtindia_v6/"
# ----------------------------------------------------------------

# Cache settings
USE_CACHE_IF_FAIL = True
CACHE_FILE = Path("ecourts_homepage.html")


def create_driver(headless: bool = True) -> webdriver.Chrome:
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--enable-features=NetworkServiceInProcess")  # Speed up network handling

    # Mimic real browser to avoid throttling
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36")

    service = Service()  # Assumes chromedriver on PATH

    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


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
            return

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = CSV_FOLDER / f"case_history_{CNR_NUMBER}_{ts}.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "Judge",
                    "Business_on_Date",
                    "Hearing_Date",
                    "Purpose_of_Hearing",
                ],
            )
            writer.writeheader()
            writer.writerows(history)

        print(f"✅  Saved {len(history)} rows to {csv_path}")
        print(f"Total runtime: {time.perf_counter() - start_time:.2f}s")

    except Exception as e:
        print(f"Error: {e}")
        print("Page source snippet:\n", driver.page_source[:500])

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
