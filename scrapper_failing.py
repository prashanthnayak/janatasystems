import requests
import numpy as np
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import cv2
import os
from datetime import datetime
import sys
import torchvision
# import whisper
# import torch

def scrape_case_details(cnr_number):
    """
    Scrape case details from eCourts for a given CNR number
    Returns a dictionary with case information
    """
    max_retries = 3
    
    for attempt in range(max_retries):
        print(f"🔄 Scraping attempt {attempt + 1}/{max_retries} for CNR: {cnr_number}")
        
        driver = create_chrome_driver(headless=True)
        if not driver:
            if attempt < max_retries - 1:
                print("❌ Failed to create Chrome driver, retrying...")
                time.sleep(2)
                continue
            else:
                return {'success': False, 'error': 'Failed to create Chrome driver after multiple attempts'}
        
        try:
            print(f"Starting scraping for CNR: {cnr_number}")
            
            # Navigate to eCourts
            driver.get("https://services.ecourts.gov.in/ecourtindia_v6/")
            time.sleep(3)
            
            # Debug: Print page title and available form elements
            print(f"Page title: {driver.title}")
            print("Available form elements:")
            try:
                inputs = driver.find_elements(By.TAG_NAME, "input")
                for i, inp in enumerate(inputs):
                    print(f"  Input {i}: id='{inp.get_attribute('id')}', name='{inp.get_attribute('name')}', placeholder='{inp.get_attribute('placeholder')}'")
                
                buttons = driver.find_elements(By.TAG_NAME, "button")
                for i, btn in enumerate(buttons):
                    print(f"  Button {i}: id='{btn.get_attribute('id')}', text='{btn.text}'")
            except Exception as e:
                print(f"Error listing elements: {e}")
            
            # Save CAPTCHA
            captcha_path = save_captcha_image(driver)
            if not captcha_path:
                if attempt < max_retries - 1:
                    print("❌ Failed to save CAPTCHA, retrying entire process...")
                    driver.quit()
                    time.sleep(2)
                    continue
                else:
                    driver.quit()
                    return {'success': False, 'error': 'Failed to save CAPTCHA after multiple attempts'}
            
            # Solve CAPTCHA
            solved_captcha = solve_captcha(captcha_path)
            if not solved_captcha:
                if attempt < max_retries - 1:
                    print("❌ Failed to solve CAPTCHA, retrying entire process...")
                    driver.quit()
                    time.sleep(2)
                    continue
                else:
                    driver.quit()
                    return {'success': False, 'error': 'Failed to solve CAPTCHA after multiple attempts'}
            
            # Fill form and submit - try different possible element IDs
            cnr_input = None
            captcha_input = None
            submit_button = None
            
            # Try different possible CNR input field IDs
            possible_cnr_ids = ['cnr_number', 'cnr', 'case_number', 'case_no', 'cnr_no', 'cino']
            for cnr_id in possible_cnr_ids:
                try:
                    cnr_input = driver.find_element(By.ID, cnr_id)
                    print(f"Found CNR input field with ID: {cnr_id}")
                    break
                except:
                    continue
            
            # Try different possible CAPTCHA input field IDs
            possible_captcha_ids = ['captcha', 'fcaptcha_code', 'captcha_code', 'captcha_input']
            for captcha_id in possible_captcha_ids:
                try:
                    captcha_input = driver.find_element(By.ID, captcha_id)
                    print(f"Found CAPTCHA input field with ID: {captcha_id}")
                    break
                except:
                    continue
            
            # Try different possible submit button IDs
            possible_submit_ids = ['searchbtn', 'search_btn', 'submit', 'submit_btn', 'search']
            for submit_id in possible_submit_ids:
                try:
                    submit_button = driver.find_element(By.ID, submit_id)
                    print(f"Found submit button with ID: {submit_id}")
                    break
                except:
                    continue
            
            # If we can't find elements by ID, try by name or other selectors
            if not cnr_input:
                try:
                    cnr_input = driver.find_element(By.NAME, 'cnr_number')
                    print("Found CNR input field by name")
                except:
                    try:
                        cnr_input = driver.find_element(By.XPATH, "//input[@placeholder*='CNR' or @placeholder*='Case']")
                        print("Found CNR input field by placeholder")
                    except:
                        print("Could not find CNR input field")
                        if attempt < max_retries - 1:
                            print("❌ Retrying entire process...")
                            driver.quit()
                            time.sleep(2)
                            continue
                        else:
                            driver.quit()
                            return {'success': False, 'error': 'CNR input field not found'}
            
            if not captcha_input:
                try:
                    captcha_input = driver.find_element(By.NAME, 'captcha')
                    print("Found CAPTCHA input field by name")
                except:
                    try:
                        captcha_input = driver.find_element(By.XPATH, "//input[@placeholder*='CAPTCHA' or @placeholder*='code']")
                        print("Found CAPTCHA input field by placeholder")
                    except:
                        print("Could not find CAPTCHA input field")
                        if attempt < max_retries - 1:
                            print("❌ Retrying entire process...")
                            driver.quit()
                            time.sleep(2)
                            continue
                        else:
                            driver.quit()
                            return {'success': False, 'error': 'CAPTCHA input field not found'}
            
            if not submit_button:
                try:
                    submit_button = driver.find_element(By.XPATH, "//button[@type='submit' or contains(text(), 'Search') or contains(text(), 'Submit')]")
                    print("Found submit button by text")
                except:
                    print("Could not find submit button")
                    if attempt < max_retries - 1:
                        print("❌ Retrying entire process...")
                        driver.quit()
                        time.sleep(2)
                        continue
                    else:
                        driver.quit()
                        return {'success': False, 'error': 'Submit button not found'}
            
            # Fill the form
            cnr_input.clear()
            cnr_input.send_keys(cnr_number)
            
            captcha_input.clear()
            captcha_input.send_keys(solved_captcha)
            
            submit_button.click()
            
            # Wait longer for the page to load and check if we got the case details
            print("Waiting for page to load after form submission...")
            time.sleep(10)  # Increased wait time
            
            # Check if we successfully got to the case details page
            try:
                # Look for case details or error message
                page_source = driver.page_source.lower()
                if 'case details' in page_source or 'case history' in page_source or 'history_table' in page_source:
                    print("✅ Successfully reached case details page")
                    break
                elif 'invalid captcha' in page_source or 'wrong captcha' in page_source or 'captcha error' in page_source:
                    print("❌ CAPTCHA was incorrect, retrying entire process...")
                    if attempt < max_retries - 1:
                        driver.quit()
                        time.sleep(2)
                        continue
                    else:
                        driver.quit()
                        return {'success': False, 'error': 'CAPTCHA verification failed after multiple attempts'}
                else:
                    print("Unknown page state, checking for case data...")
                    # Try to extract case details anyway
                    case_data = extract_case_details(driver)
                    if case_data.get('case_title') and case_data.get('case_title') != 'Unknown':
                        print("✅ Found case data despite unknown page state")
                        break
                    else:
                        print("❌ No case data found, retrying entire process...")
                        if attempt < max_retries - 1:
                            driver.quit()
                            time.sleep(2)
                            continue
                        else:
                            driver.quit()
                            return {'success': False, 'error': 'No case data found after multiple attempts'}
            except Exception as e:
                print(f"❌ Error checking page state: {e}")
                if attempt < max_retries - 1:
                    print("❌ Retrying entire process...")
                    driver.quit()
                    time.sleep(2)
                    continue
                else:
                    driver.quit()
                    return {'success': False, 'error': f'Error checking page state: {str(e)}'}
            
        except Exception as e:
            print(f"❌ Scraping error for {cnr_number}: {e}")
            if attempt < max_retries - 1:
                print("❌ Retrying entire process...")
                driver.quit()
                time.sleep(2)
                continue
            else:
                driver.quit()
                return {'success': False, 'error': str(e)}
        finally:
            if driver:
                driver.quit()
    
    # Extract case details
    print(f"🔍 Extracting case details from page for CNR: {cnr_number}")
    case_data = extract_case_details(driver)
    print(f"📊 Extracted case data: {case_data}")
    
    result = {
        'success': True,
        'cnr_number': cnr_number,
        **case_data
    }
    print(f"✅ Final result for CNR {cnr_number}: {result}")
    
    return result

def extract_case_details(driver):
    """Extract case details from the results page"""
    print("🔍 Starting case details extraction...")
    try:
        wait = WebDriverWait(driver, 10)
        
        # Extract basic case information
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
        print("🔍 Initial case data structure created")
        
        # Try to extract case title
        try:
            title_element = driver.find_element(By.XPATH, "//td[contains(text(), 'Case Title')]/following-sibling::td")
            case_data['case_title'] = title_element.text.strip()
            print(f"✅ Extracted case title: {case_data['case_title']}")
        except:
            print("❌ Failed to extract case title")
            pass
        
        # Try to extract petitioner
        try:
            petitioner_element = driver.find_element(By.XPATH, "//td[contains(text(), 'Petitioner')]/following-sibling::td")
            case_data['petitioner'] = petitioner_element.text.strip()
            print(f"✅ Extracted petitioner: {case_data['petitioner']}")
        except:
            print("❌ Failed to extract petitioner")
            pass
        
        # Try to extract respondent
        try:
            respondent_element = driver.find_element(By.XPATH, "//td[contains(text(), 'Respondent')]/following-sibling::td")
            case_data['respondent'] = respondent_element.text.strip()
            print(f"✅ Extracted respondent: {case_data['respondent']}")
        except:
            print("❌ Failed to extract respondent")
            pass
        
        # Try to extract case type
        try:
            case_type_element = driver.find_element(By.XPATH, "//td[contains(text(), 'Case Type')]/following-sibling::td")
            case_data['case_type'] = case_type_element.text.strip()
            print(f"✅ Extracted case type: {case_data['case_type']}")
        except:
            print("❌ Failed to extract case type")
            pass
        
        # Try to extract court name
        try:
            court_element = driver.find_element(By.XPATH, "//td[contains(text(), 'Court')]/following-sibling::td")
            case_data['court_name'] = court_element.text.strip()
            print(f"✅ Extracted court name: {case_data['court_name']}")
        except:
            print("❌ Failed to extract court name")
            pass
        
        # Try to extract judge name
        try:
            judge_element = driver.find_element(By.XPATH, "//td[contains(text(), 'Judge')]/following-sibling::td")
            case_data['judge_name'] = judge_element.text.strip()
            print(f"✅ Extracted judge name: {case_data['judge_name']}")
        except:
            print("❌ Failed to extract judge name")
            pass
        
        # Try to extract filing date
        try:
            filing_date_element = driver.find_element(By.XPATH, "//td[contains(text(), 'Filing Date')]/following-sibling::td")
            case_data['filing_date'] = filing_date_element.text.strip()
            print(f"✅ Extracted filing date: {case_data['filing_date']}")
        except:
            print("❌ Failed to extract filing date")
            pass
        
        # Try to extract registration number
        try:
            reg_element = driver.find_element(By.XPATH, "//td[contains(text(), 'Registration Number')]/following-sibling::td")
            case_data['registration_number'] = reg_element.text.strip()
            print(f"✅ Extracted registration number: {case_data['registration_number']}")
        except:
            print("❌ Failed to extract registration number")
            pass
        
        print(f"📊 Final extracted case data: {case_data}")
        return case_data
        
    except Exception as e:
        print(f"❌ Error extracting case details: {e}")
        return {
            'case_title': 'Error extracting data',
            'petitioner': 'Unknown',
            'respondent': 'Unknown',
            'case_type': 'Civil',
            'court_name': 'Unknown Court',
            'judge_name': 'Unknown Judge',
            'status': 'Active',
            'filing_date': None,
            'registration_number': 'Unknown'
        }

def solve_captcha(captcha_image_path):
    """
    Solve CAPTCHA using OCR
    Returns the solved CAPTCHA text or None if failed
    """
    try:
        from transformers import VisionEncoderDecoderModel, TrOCRProcessor
        import torch
        from PIL import Image

        print(f"Solving CAPTCHA: {captcha_image_path}")
        
        model_name = 'anuashok/ocr-captcha-v3'
        processor = TrOCRProcessor.from_pretrained(model_name)
        model = VisionEncoderDecoderModel.from_pretrained(model_name)

        image = Image.open(captcha_image_path).convert("RGBA")
        background = Image.new("RGBA", image.size, (255, 255, 255))
        combined = Image.alpha_composite(background, image).convert("RGB")

        pixel_values = processor(combined, return_tensors="pt").pixel_values
        generated_ids = model.generate(pixel_values)
        ocr_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        print(f"CAPTCHA solved: {ocr_text}")
        return ocr_text.strip()
        
    except Exception as e:
        print(f"Failed to solve CAPTCHA: {e}")
        return None

def create_chrome_driver(headless=True):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")
    if sys.platform == "darwin":
        chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    elif sys.platform.startswith("linux"):
        chrome_options.binary_location = "/usr/bin/chromium-browser"
    # For Windows, you can add another elif
    try:
        driver = webdriver.Chrome(options=chrome_options)
        print("Chrome driver created successfully.")
        return driver
    except Exception as e:
        print(f"Error creating driver: {e}")
        return None

# Function to save CAPTCHA image
def save_captcha_image(driver, save_directory=os.path.expanduser("~/Desktop/captcha_images")):
    wait = WebDriverWait(driver, 1)
    try:
        # Create directory if it doesn't exist
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)
            print(f"Created directory: {save_directory}")
        
        captcha_img = wait.until(EC.presence_of_element_located((By.ID, 'captcha_image')))
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"captcha_{timestamp}.png"
        filepath = os.path.join(save_directory, filename)

        # Take a screenshot of the CAPTCHA element
        captcha_img.screenshot(filepath)

        print(f"CAPTCHA image saved as: {filepath}")
        
        # # Also save CAPTCHA audio
        # try:
        #     # Method 1: Try to download the audio file directly
        #     audio_element = driver.find_element(By.ID, 'captcha_image_audio')
        #     audio_source = audio_element.find_element(By.TAG_NAME, 'source')
        #     audio_src = audio_source.get_attribute('src')
            
        #     # Convert relative URL to absolute URL
        #     if audio_src.startswith('/'):
        #         audio_src = "https://services.ecourts.gov.in" + audio_src
            
        #     print(f"Attempting to download audio from: {audio_src}")
            
        #     # Download audio file
        #     audio_response = requests.get(audio_src)
            
        #     if audio_response.status_code == 200 and len(audio_response.content) > 0:
        #         audio_filename = f"captcha_{timestamp}.wav"
        #         audio_filepath = os.path.join(save_directory, audio_filename)
                
        #         with open(audio_filepath, 'wb') as f:
        #             f.write(audio_response.content)
                
        #         print(f"CAPTCHA audio saved as: {audio_filepath}")
        #         print(f"Audio file size: {len(audio_response.content)} bytes")
        #     else:
        #         print(f"Audio download failed. Status: {audio_response.status_code}")
        #         print("Audio might be a stream or require session authentication")
                
        # except Exception as e:
        #     print(f"Could not save CAPTCHA audio: {e}")
        #     print("Audio capture failed - this is normal if audio is streamed dynamically")
        
        return filepath

    except PermissionError as e:
        print(f"Permission denied: {e}")
        return None
    except Exception as e:
        print(f"Failed to save CAPTCHA image: {e}")
        return None

# # Function to transcribe audio using Whisper
# def transcribe_audio(audio_file_path, model_name="base"):
#     """
#     Transcribe audio file using OpenAI's Whisper model
#     
#     Args:
#         audio_file_path (str): Path to the audio file
#         model_name (str): Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
#     
#     Returns:
#         str: Transcribed text
#     """
#     try:
#         print(f"Loading Whisper model: {model_name}")
#         model = whisper.load_model(model_name)
#         
#         print(f"Transcribing audio file: {audio_file_path}")
#         result = model.transcribe(audio_file_path)
#         
#         transcribed_text = result["text"].strip()
#         print(f"Transcription completed: '{transcribed_text}'")
#         
#         return transcribed_text
#         
#     except Exception as e:
#         print(f"Error transcribing audio: {e}")
#         return None

# # Function to solve CAPTCHA using audio transcription
# def solve_captcha_audio(audio_file_path):
#     """
#     Solve CAPTCHA by transcribing audio and extracting numbers/letters
#     
#     Args:
#         audio_file_path (str): Path to the CAPTCHA audio file
#     
#     Returns:
#         str: Extracted CAPTCHA text
#     """
#     try:
#         # Transcribe the audio
#         transcription = transcribe_audio(audio_file_path, model_name="base")
#         
#         if transcription:
#             # Clean up the transcription - extract only alphanumeric characters
#             import re
#             captcha_text = re.sub(r'[^a-zA-Z0-9]', '', transcription.upper())
#             
#             print(f"Extracted CAPTCHA text: {captcha_text}")
#             return captcha_text
#         else:
#             print("Failed to transcribe audio")
#             return None
#             
#     except Exception as e:
#         print(f"Error solving CAPTCHA with audio: {e}")
#         return None

# Main script
driver = create_chrome_driver(headless=False)  # Set to False for local testing
if driver:
    try:
        driver.get("https://services.ecourts.gov.in/ecourtindia_v6/")
        time.sleep(1)

        # Enter CNR
        wait = WebDriverWait(driver, 1)
        cnr_input = wait.until(EC.presence_of_element_located((By.ID, 'cino')))
        cnr_number = "KAUP050003552024"  # e.g., MHAU019999992015
        cnr_input.clear()
        cnr_input.send_keys(cnr_number)
        print(f"Entered CNR number: {cnr_number}")

        # Save CAPTCHA image and audio
        saved_image_path = save_captcha_image(driver)

        if saved_image_path:
            print(f"CAPTCHA image successfully saved to: {saved_image_path}")
            print("Attempting to solve CAPTCHA...")

            ocr_text = None
            audio_text = None
            
            # Try OCR first
            try:
                from transformers import VisionEncoderDecoderModel, TrOCRProcessor
                import torch
                from PIL import Image

                model_name = 'anuashok/ocr-captcha-v3'
                processor = TrOCRProcessor.from_pretrained(model_name)
                model = VisionEncoderDecoderModel.from_pretrained(model_name)

                image = Image.open(saved_image_path).convert("RGBA")
                background = Image.new("RGBA", image.size, (255, 255, 255))
                combined = Image.alpha_composite(background, image).convert("RGB")

                pixel_values = processor(combined, return_tensors="pt").pixel_values
                generated_ids = model.generate(pixel_values)
                ocr_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
                print("Predicted CAPTCHA text (OCR):", ocr_text)
                
            except Exception as e:
                print(f"OCR failed: {e}")
                ocr_text = None
            
            # Always try audio transcription as well
            # print("\n" + "="*50)
            # print("AUDIO TRANSCRIPTION ATTEMPT")
            # print("="*50)
            
            # # Look for audio file in the same directory
            # audio_directory = os.path.dirname(saved_image_path)
            # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # audio_filename = f"captcha_{timestamp}.wav"
            # audio_filepath = os.path.join(audio_directory, audio_filename)
            
            # if os.path.exists(audio_filepath):
            #     print(f"Found audio file: {audio_filepath}")
            #     audio_text = solve_captcha_audio(audio_filepath)
            #     if audio_text:
            #         print(f"Predicted CAPTCHA text (Audio): {audio_text}")
            #     else:
            #         print("Audio transcription failed")
            # else:
            #     print(f"Audio file not found: {audio_filepath}")
            #     print("Available files in directory:")
            #     for file in os.listdir(audio_directory):
            #         if file.endswith('.wav'):
            #             print(f"  - {file}")
            
            # # Print comparison summary
            # print("\n" + "="*50)
            # print("CAPTCHA SOLVING RESULTS")
            # print("="*50)
            # print(f"OCR Result:     {ocr_text if ocr_text else 'FAILED'}")
            # print(f"Audio Result:   {audio_text if audio_text else 'FAILED'}")
            
            # # Choose the best result (prefer OCR if both available)
            # if ocr_text and len(ocr_text.strip()) > 0:
            #     generated_text = ocr_text
            #     print(f"Using OCR result: {generated_text}")
            # elif audio_text and len(audio_text.strip()) > 0:
            #     generated_text = audio_text
            #     print(f"Using Audio result: {generated_text}")
            # else:
            #     print("Both methods failed. Cannot proceed.")
            #     generated_text = "FAILED"  # Set a fallback value
            
            # print("="*50)
            
            # Simplified version - use OCR result only
            if ocr_text and len(ocr_text.strip()) > 0:
                generated_text = ocr_text
                print(f"Using OCR result: {generated_text}")
            else:
                print("OCR failed. Cannot proceed.")
                generated_text = "FAILED"  # Set a fallback value

            # Automatically enter the solved CAPTCHA and press search
            try:
                captcha_input = driver.find_element(By.ID, 'fcaptcha_code')
                captcha_input.clear()
                captcha_input.send_keys(generated_text)
                print(f"Entered solved CAPTCHA: {generated_text}")

                submit_button = wait.until(EC.element_to_be_clickable((By.ID, 'searchbtn')))
                submit_button.click()
                print("Search button clicked. Waiting for results...")
                time.sleep(5)  # Wait for results to load
                
                # Extract case history and details
                try:
                    print("Extracting case history data...")
                    
                    # Wait for the case history table to load
                    wait = WebDriverWait(driver, 15)
                    
                    # Extract case history from history_table
                    case_history = []
                    try:
                        history_table = driver.find_element(By.CLASS_NAME, 'history_table')
                        rows = history_table.find_elements(By.TAG_NAME, 'tr')
                        
                        print(f"\n{'='*80}")
                        print("CASE HISTORY TABLE")
                        print(f"{'='*80}")
                        print(f"{'Judge':<40} {'Business Date':<15} {'Hearing Date':<15} {'Purpose':<20}")
                        print(f"{'-'*40} {'-'*15} {'-'*15} {'-'*20}")
                        
                        for row in rows[1:]:  # Skip header row
                            cells = row.find_elements(By.TAG_NAME, 'td')
                            if len(cells) >= 4:
                                judge = cells[0].text.strip()
                                business_date = cells[1].text.strip()
                                hearing_date = cells[2].text.strip()
                                purpose = cells[3].text.strip()
                                
                                history_entry = {
                                    'Judge': judge,
                                    'Business_on_Date': business_date,
                                    'Hearing_Date': hearing_date,
                                    'Purpose_of_Hearing': purpose
                                }
                                case_history.append(history_entry)
                                
                                # Print formatted row
                                print(f"{judge:<40} {business_date:<15} {hearing_date:<15} {purpose:<20}")
                        
                        print(f"{'='*80}")
                        print(f"Total History Entries: {len(case_history)}")
                        print(f"{'='*80}")
                        
                    except Exception as e:
                        print(f"Could not extract case history: {e}")
                    
                    # Save case history to CSV file
                    if case_history:
                        import csv
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        csv_filename = f"case_history_{cnr_number}_{timestamp}.csv"
                        
                        # Save to shantharam directory
                        import os
                        save_directory = "/Users/prashanth/Desktop/shantharam"
                        full_path = os.path.join(save_directory, csv_filename)
                        print(f"\nSaving CSV file to: {full_path}")
                        
                        with open(full_path, 'w', newline='', encoding='utf-8') as csvfile:
                            writer = csv.writer(csvfile)
                            
                            # Write header
                            writer.writerow(['Judge', 'Business_on_Date', 'Hearing_Date', 'Purpose_of_Hearing'])
                            
                            # Write data
                            for entry in case_history:
                                writer.writerow([
                                    entry['Judge'],
                                    entry['Business_on_Date'],
                                    entry['Hearing_Date'],
                                    entry['Purpose_of_Hearing']
                                ])
                        
                        print(f"\nCase history saved to: {csv_filename}")
                    
                except Exception as e:
                    print(f"Failed to extract case data: {e}")

            except Exception as e:
                print(f"Failed to submit CAPTCHA and search: {e}")

        else:
            print("Failed to save CAPTCHA image.")

    except Exception as e:
        print(f"Script error: {e}")
        print("Partial page source:\n", driver.page_source[:1000])
    finally:
        print("Waiting 60 seconds before closing browser...")
        time.sleep(5)  # Wait for 1 minute
        driver.quit()
        print("Browser session closed.")
else:
    print("Failed to create Chrome driver.")