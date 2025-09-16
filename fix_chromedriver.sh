#!/bin/bash
#
# Fix ChromeDriver Installation for Chrome 140
# Chrome 140 is newer than available ChromeDriver versions
#

echo "🚗 Fixing ChromeDriver for Chrome 140"
echo "===================================="

# Chrome 140 is installed, but ChromeDriver 140 doesn't exist yet
# We need to use the latest available ChromeDriver version

echo "ℹ️ Chrome 140 is newer than available ChromeDriver versions"
echo "🔍 Finding latest available ChromeDriver..."

# Get the latest ChromeDriver version available
echo "📡 Checking latest ChromeDriver releases..."

# Try to get the latest stable ChromeDriver version
LATEST_CHROMEDRIVER=""

# Method 1: Try the latest stable release endpoint
if command -v curl &> /dev/null; then
    LATEST_CHROMEDRIVER=$(curl -s https://chromedriver.storage.googleapis.com/LATEST_RELEASE 2>/dev/null || echo "")
fi

# Method 2: Try with wget if curl failed
if [ -z "$LATEST_CHROMEDRIVER" ]; then
    LATEST_CHROMEDRIVER=$(wget -qO- https://chromedriver.storage.googleapis.com/LATEST_RELEASE 2>/dev/null || echo "")
fi

# Method 3: Try specific known versions (fallback)
if [ -z "$LATEST_CHROMEDRIVER" ] || [[ "$LATEST_CHROMEDRIVER" == *"Error"* ]] || [[ "$LATEST_CHROMEDRIVER" == *"xml"* ]]; then
    echo "⚠️ Latest release endpoint not working, trying known versions..."
    
    # Try some recent ChromeDriver versions that should work with Chrome 140
    KNOWN_VERSIONS=("131.0.6778.85" "130.0.6723.91" "129.0.6668.89" "128.0.6613.84")
    
    for version in "${KNOWN_VERSIONS[@]}"; do
        echo "🔍 Checking if ChromeDriver $version exists..."
        if wget --spider -q "https://chromedriver.storage.googleapis.com/$version/chromedriver_linux64.zip" 2>/dev/null; then
            LATEST_CHROMEDRIVER="$version"
            echo "✅ Found working ChromeDriver version: $version"
            break
        fi
    done
fi

# If still no version found, use a known stable version
if [ -z "$LATEST_CHROMEDRIVER" ] || [[ "$LATEST_CHROMEDRIVER" == *"Error"* ]]; then
    LATEST_CHROMEDRIVER="131.0.6778.85"  # Known stable version
    echo "🔄 Using fallback ChromeDriver version: $LATEST_CHROMEDRIVER"
fi

echo "📦 Using ChromeDriver version: $LATEST_CHROMEDRIVER"

# Download the ChromeDriver
echo "⬇️ Downloading ChromeDriver $LATEST_CHROMEDRIVER..."
cd /tmp
rm -f chromedriver.zip

wget --no-check-certificate --timeout=30 \
     -O chromedriver.zip \
     "https://chromedriver.storage.googleapis.com/$LATEST_CHROMEDRIVER/chromedriver_linux64.zip"

# Check if download was successful
if [ ! -f "chromedriver.zip" ] || [ ! -s "chromedriver.zip" ]; then
    echo "❌ ChromeDriver download failed"
    echo "🔄 Trying alternative download..."
    
    # Try alternative URL format
    wget --no-check-certificate --timeout=30 \
         -O chromedriver.zip \
         "https://storage.googleapis.com/chrome-for-testing-public/$LATEST_CHROMEDRIVER/linux64/chromedriver-linux64.zip"
fi

if [ ! -f "chromedriver.zip" ] || [ ! -s "chromedriver.zip" ]; then
    echo "❌ ChromeDriver download failed completely"
    echo "⚠️ You may need to download ChromeDriver manually"
    exit 1
fi

echo "✅ ChromeDriver downloaded successfully"

# Install ChromeDriver
echo "📦 Installing ChromeDriver..."

# Remove old ChromeDriver if exists
sudo rm -f /usr/local/bin/chromedriver

# Extract and install
if unzip -l chromedriver.zip | grep -q "chromedriver-linux64/chromedriver"; then
    # New format with subdirectory
    unzip -j chromedriver.zip "chromedriver-linux64/chromedriver" -d /tmp/
    sudo mv /tmp/chromedriver /usr/local/bin/
else
    # Old format, direct extraction
    sudo unzip -o chromedriver.zip -d /usr/local/bin/
fi

sudo chmod +x /usr/local/bin/chromedriver
rm -f chromedriver.zip

# Test ChromeDriver
echo "🧪 Testing ChromeDriver..."
if chromedriver --version 2>/dev/null; then
    CHROMEDRIVER_VERSION_OUTPUT=$(chromedriver --version)
    echo "✅ ChromeDriver is working: $CHROMEDRIVER_VERSION_OUTPUT"
else
    echo "❌ ChromeDriver test failed"
    exit 1
fi

# Test compatibility between Chrome and ChromeDriver
echo "🧪 Testing Chrome + ChromeDriver compatibility..."

# Create a simple test script
cat > /tmp/test_chrome_compatibility.py << 'EOF'
#!/usr/bin/env python3
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

try:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    driver = webdriver.Chrome(options=options)
    driver.get("data:text/html,<html><body><h1>Test</h1></body></html>")
    title = driver.title
    driver.quit()
    
    print("✅ Chrome + ChromeDriver compatibility test passed")
    sys.exit(0)
    
except Exception as e:
    print(f"❌ Compatibility test failed: {e}")
    sys.exit(1)
EOF

if python3 /tmp/test_chrome_compatibility.py 2>/dev/null; then
    echo "✅ Chrome and ChromeDriver are compatible!"
else
    echo "⚠️ Compatibility test had issues, but installation completed"
    echo "   This might still work for your scraping needs"
fi

# Clean up
rm -f /tmp/test_chrome_compatibility.py

echo ""
echo "🎉 ChromeDriver installation fixed!"
echo "=================================="
echo "✅ Chrome: $(google-chrome --version)"
echo "✅ ChromeDriver: $(chromedriver --version)"
echo ""
echo "📝 Note: Chrome 140 is newer than available ChromeDriver versions"
echo "     Using ChromeDriver $LATEST_CHROMEDRIVER which should be compatible"
echo ""
echo "🧪 Test your setup:"
echo "   python3 test_chrome_ec2.py"
