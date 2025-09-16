#!/usr/bin/env python3
"""
Simple test to check what's failing in the scraping process
"""

import sys
import traceback

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from selenium import webdriver
        print("✅ Selenium imported")
    except Exception as e:
        print(f"❌ Selenium import failed: {e}")
        return False
    
    try:
        from PIL import Image
        print("✅ PIL imported")
    except Exception as e:
        print(f"❌ PIL import failed: {e}")
        return False
    
    try:
        import torch
        print("✅ PyTorch imported")
    except Exception as e:
        print(f"❌ PyTorch import failed: {e}")
        return False
    
    try:
        from transformers import VisionEncoderDecoderModel, TrOCRProcessor
        print("✅ Transformers imported")
    except Exception as e:
        print(f"❌ Transformers import failed: {e}")
        return False
    
    return True

def test_chrome_driver():
    """Test Chrome driver creation"""
    print("\n🔍 Testing Chrome driver creation...")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        driver = webdriver.Chrome(options=options)
        print("✅ Chrome driver created")
        
        # Test basic navigation
        driver.get("data:text/html,<html><body><h1>Test</h1></body></html>")
        print("✅ Basic navigation works")
        
        driver.quit()
        print("✅ Chrome driver closed properly")
        return True
        
    except Exception as e:
        print(f"❌ Chrome driver test failed: {e}")
        traceback.print_exc()
        return False

def test_ocr_model():
    """Test OCR model loading"""
    print("\n🔍 Testing OCR model loading...")
    
    try:
        from transformers import VisionEncoderDecoderModel, TrOCRProcessor
        
        model_name = "anuashok/ocr-captcha-v3"
        print(f"📦 Loading model: {model_name}")
        
        processor = TrOCRProcessor.from_pretrained(model_name)
        print("✅ Processor loaded")
        
        model = VisionEncoderDecoderModel.from_pretrained(model_name)
        print("✅ Model loaded")
        
        return True
        
    except Exception as e:
        print(f"❌ OCR model test failed: {e}")
        traceback.print_exc()
        return False

def test_scraper_import():
    """Test importing the scraper module"""
    print("\n🔍 Testing scraper module import...")
    
    try:
        import scrapper
        print("✅ Scrapper module imported")
        
        # Test the main function exists
        if hasattr(scrapper, 'scrape_case_details'):
            print("✅ scrape_case_details function found")
        else:
            print("❌ scrape_case_details function not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Scrapper import failed: {e}")
        traceback.print_exc()
        return False

def test_actual_scraping():
    """Test actual scraping with a sample CNR"""
    print("\n🔍 Testing actual scraping...")
    
    try:
        import scrapper
        
        # Use a test CNR number
        test_cnr = "KAUP050003552024"
        print(f"🧪 Testing with CNR: {test_cnr}")
        
        result = scrapper.scrape_case_details(test_cnr)
        
        if isinstance(result, dict):
            if result.get('success', False):
                print("✅ Scraping completed successfully")
                print(f"📊 Result keys: {list(result.keys())}")
                return True
            else:
                print(f"❌ Scraping failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Unexpected result type: {type(result)}")
            return False
        
    except Exception as e:
        print(f"❌ Actual scraping test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🧪 Starting comprehensive scraping tests")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Chrome Driver Test", test_chrome_driver),
        ("OCR Model Test", test_ocr_model),
        ("Scraper Import Test", test_scraper_import),
        ("Actual Scraping Test", test_actual_scraping)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} CRASHED: {e}")
    
    print(f"\n{'='*50}")
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Scraping should work.")
    else:
        print(f"⚠️ {total - passed} tests failed. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
