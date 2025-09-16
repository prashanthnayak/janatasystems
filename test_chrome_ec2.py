#!/usr/bin/env python3
"""
Test Chrome/Selenium setup on EC2
This script tests if Chrome and ChromeDriver work properly in headless mode
"""

import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

def test_chrome_basic():
    """Test basic Chrome functionality"""
    print("🔍 Testing basic Chrome setup...")
    
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        print("📦 Creating Chrome driver...")
        driver = webdriver.Chrome(options=chrome_options)
        
        print("🌐 Loading test page...")
        driver.get("data:text/html,<html><body><h1>Test Page</h1><p>Chrome is working!</p></body></html>")
        
        # Get page title
        title = driver.title
        print(f"✅ Page title: {title}")
        
        # Get page source
        source = driver.page_source
        if "Test Page" in source:
            print("✅ Page content loaded correctly")
        else:
            print("❌ Page content not loaded")
            return False
        
        driver.quit()
        print("✅ Basic Chrome test passed")
        return True
        
    except Exception as e:
        print(f"❌ Basic Chrome test failed: {e}")
        return False

def test_chrome_real_website():
    """Test Chrome with a real website"""
    print("\n🌐 Testing Chrome with real website...")
    
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        driver = webdriver.Chrome(options=chrome_options)
        
        print("📡 Loading Google.com...")
        driver.get("https://www.google.com")
        
        # Wait a moment for page to load
        time.sleep(2)
        
        title = driver.title
        print(f"✅ Page title: {title}")
        
        if "Google" in title:
            print("✅ Real website test passed")
            result = True
        else:
            print("❌ Unexpected page title")
            result = False
        
        driver.quit()
        return result
        
    except Exception as e:
        print(f"❌ Real website test failed: {e}")
        return False

def test_chrome_ecourts():
    """Test Chrome with e-courts website"""
    print("\n⚖️ Testing Chrome with e-courts website...")
    
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        driver = webdriver.Chrome(options=chrome_options)
        
        print("📡 Loading e-courts website...")
        driver.get("https://services.ecourts.gov.in/ecourtindia_v6/")
        
        # Wait for page to load
        time.sleep(5)
        
        title = driver.title
        print(f"✅ Page title: {title}")
        
        # Check if page loaded properly
        source = driver.page_source
        if "eCourts" in source or "CNR" in source:
            print("✅ E-courts website loaded successfully")
            result = True
        else:
            print("❌ E-courts website may not have loaded properly")
            print(f"Page source length: {len(source)} characters")
            result = False
        
        driver.quit()
        return result
        
    except Exception as e:
        print(f"❌ E-courts test failed: {e}")
        return False

def check_system_requirements():
    """Check system requirements"""
    print("🔍 Checking system requirements...")
    
    # Check Chrome
    try:
        import subprocess
        result = subprocess.run(['google-chrome', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Chrome: {result.stdout.strip()}")
        else:
            print("❌ Chrome not found or not working")
            return False
    except:
        print("❌ Chrome not found")
        return False
    
    # Check ChromeDriver
    try:
        result = subprocess.run(['chromedriver', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ ChromeDriver: {result.stdout.strip()}")
        else:
            print("❌ ChromeDriver not found or not working")
            return False
    except:
        print("❌ ChromeDriver not found")
        return False
    
    # Check display
    import os
    display = os.environ.get('DISPLAY')
    if display:
        print(f"ℹ️ DISPLAY environment variable: {display}")
    else:
        print("ℹ️ No DISPLAY environment variable (normal for headless)")
    
    return True

def main():
    """Run all tests"""
    print("🧪 Chrome/Selenium EC2 Compatibility Test")
    print("=" * 50)
    
    # Check system requirements
    if not check_system_requirements():
        print("\n❌ System requirements not met")
        return False
    
    print("\n" + "=" * 50)
    
    # Run tests
    tests = [
        ("Basic Chrome Test", test_chrome_basic),
        ("Real Website Test", test_chrome_real_website),
        ("E-Courts Test", test_chrome_ecourts)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Chrome scraping should work on EC2.")
        return True
    else:
        print("⚠️ Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
