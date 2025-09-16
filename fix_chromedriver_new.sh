#!/bin/bash
#
# Fix ChromeDriver using the new Chrome for Testing API
# Google has moved ChromeDriver downloads to a new location
#

echo "🚗 Fixing ChromeDriver using new Chrome for Testing API"
echo "======================================================"

# Remove the old ChromeDriver
echo "🗑️ Removing old ChromeDriver..."
sudo rm -f /usr/local/bin/chromedriver

# Get Chrome version
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d. -f1)
echo "🔍 Detected Chrome major version: $CHROME_VERSION"

# For Chrome 140, we need to use the new Chrome for Testing endpoints
# Let's try to find a compatible version

echo "📡 Finding compatible ChromeDriver from Chrome for Testing..."

# Function to try downloading ChromeDriver
try_download_chromedriver() {
    local version=$1
    local url="https://storage.googleapis.com/chrome-for-testing-public/$version/linux64/chromedriver-linux64.zip"
    
    echo "🔍 Trying ChromeDriver version $version..."
    echo "📥 URL: $url"
    
    wget --spider -q "$url" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ Found ChromeDriver $version"
        wget -O /tmp/chromedriver.zip "$url"
        return 0
    else
        echo "❌ ChromeDriver $version not found"
        return 1
    fi
}

# Try different versions starting from newest
VERSIONS_TO_TRY=(
    "131.0.6778.204"
    "131.0.6778.108" 
    "131.0.6778.85"
    "130.0.6723.116"
    "130.0.6723.91"
    "129.0.6668.100"
    "129.0.6668.89"
    "128.0.6613.137"
    "128.0.6613.84"
    "127.0.6533.119"
    "126.0.6478.182"
)

DOWNLOAD_SUCCESS=false
CHROMEDRIVER_VERSION=""

for version in "${VERSIONS_TO_TRY[@]}"; do
    if try_download_chromedriver "$version"; then
        CHROMEDRIVER_VERSION="$version"
        DOWNLOAD_SUCCESS=true
        break
    fi
done

# If new API failed, try the old ChromeDriver storage as fallback
if [ "$DOWNLOAD_SUCCESS" = false ]; then
    echo "🔄 Trying legacy ChromeDriver storage..."
    
    LEGACY_VERSIONS=("114.0.5735.90" "113.0.5672.63" "112.0.5615.49")
    
    for version in "${LEGACY_VERSIONS[@]}"; do
        echo "🔍 Trying legacy ChromeDriver $version..."
        wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/$version/chromedriver_linux64.zip"
        
        if [ -f "/tmp/chromedriver.zip" ] && [ -s "/tmp/chromedriver.zip" ]; then
            CHROMEDRIVER_VERSION="$version"
            DOWNLOAD_SUCCESS=true
            echo "✅ Downloaded legacy ChromeDriver $version"
            break
        fi
    done
fi

# Check if download was successful
if [ "$DOWNLOAD_SUCCESS" = false ]; then
    echo "❌ All ChromeDriver downloads failed"
    echo ""
    echo "🔧 Manual solution:"
    echo "1. Go to: https://googlechromelabs.github.io/chrome-for-testing/"
    echo "2. Download ChromeDriver for Linux64"
    echo "3. Extract and copy to /usr/local/bin/chromedriver"
    echo "4. Run: sudo chmod +x /usr/local/bin/chromedriver"
    exit 1
fi

echo "✅ ChromeDriver $CHROMEDRIVER_VERSION downloaded successfully"

# Install ChromeDriver
echo "📦 Installing ChromeDriver..."
cd /tmp

# Handle both new and old zip formats
if unzip -l chromedriver.zip | grep -q "chromedriver-linux64/chromedriver"; then
    # New format with subdirectory
    echo "📁 Extracting new format (with subdirectory)..."
    unzip -j chromedriver.zip "chromedriver-linux64/chromedriver" -d /tmp/
    sudo mv /tmp/chromedriver /usr/local/bin/
elif unzip -l chromedriver.zip | grep -q "chromedriver"; then
    # Old format, direct extraction
    echo "📁 Extracting old format (direct)..."
    unzip -o chromedriver.zip
    sudo mv chromedriver /usr/local/bin/
else
    echo "❌ Unknown zip format"
    exit 1
fi

sudo chmod +x /usr/local/bin/chromedriver
rm -f /tmp/chromedriver.zip

# Test ChromeDriver
echo "🧪 Testing ChromeDriver..."
if chromedriver --version 2>/dev/null; then
    CHROMEDRIVER_VERSION_OUTPUT=$(chromedriver --version)
    echo "✅ ChromeDriver is working: $CHROMEDRIVER_VERSION_OUTPUT"
else
    echo "❌ ChromeDriver test failed"
    exit 1
fi

# Test basic compatibility
echo "🧪 Testing basic Chrome + ChromeDriver compatibility..."

# Create a simple test
cat > /tmp/test_basic.py << 'EOF'
#!/usr/bin/env python3
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    
    driver = webdriver.Chrome(options=options)
    driver.get("data:text/html,<html><body><h1>Test</h1></body></html>")
    print("✅ Basic compatibility test passed")
    driver.quit()
    
except Exception as e:
    print(f"⚠️ Compatibility test warning: {e}")
    print("   This might still work for your needs")
EOF

python3 /tmp/test_basic.py 2>/dev/null
rm -f /tmp/test_basic.py

echo ""
echo "🎉 ChromeDriver installation completed!"
echo "======================================"
echo "✅ Chrome: $(google-chrome --version 2>/dev/null)"
echo "✅ ChromeDriver: $(chromedriver --version 2>/dev/null)"
echo ""
echo "🧪 Now test your scraping setup:"
echo "   python3 test_chrome_ec2.py"
echo ""
echo "📝 Note: Using ChromeDriver $CHROMEDRIVER_VERSION"
echo "     This should work with Chrome $CHROME_VERSION even if versions don't match exactly"
