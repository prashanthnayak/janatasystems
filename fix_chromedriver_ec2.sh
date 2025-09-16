#!/bin/bash
#
# Fix ChromeDriver on EC2 - Replace old version 114 with compatible version for Chrome 140
#

echo "🚗 Fixing ChromeDriver for Chrome 140 on EC2"
echo "============================================="

# Remove the old ChromeDriver version 114
echo "🗑️ Removing old ChromeDriver version 114..."
sudo rm -f /usr/local/bin/chromedriver

# Chrome 140 needs ChromeDriver in the 130+ range
# Let's try to get the best compatible version

echo "🔍 Finding compatible ChromeDriver version for Chrome 140..."

# Try to get ChromeDriver for version 131 (should be compatible with Chrome 140)
CHROMEDRIVER_VERSION="131.0.6778.85"

echo "📦 Using ChromeDriver version: $CHROMEDRIVER_VERSION"
echo "⬇️ Downloading ChromeDriver $CHROMEDRIVER_VERSION..."

cd /tmp
rm -f chromedriver.zip chromedriver

# Download ChromeDriver
wget --no-check-certificate --timeout=30 \
     -O chromedriver.zip \
     "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"

# Check if download was successful
if [ ! -f "chromedriver.zip" ] || [ ! -s "chromedriver.zip" ]; then
    echo "🔄 Trying alternative ChromeDriver version 130..."
    CHROMEDRIVER_VERSION="130.0.6723.91"
    wget --no-check-certificate --timeout=30 \
         -O chromedriver.zip \
         "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"
fi

# If still failed, try version 129
if [ ! -f "chromedriver.zip" ] || [ ! -s "chromedriver.zip" ]; then
    echo "🔄 Trying ChromeDriver version 129..."
    CHROMEDRIVER_VERSION="129.0.6668.89"
    wget --no-check-certificate --timeout=30 \
         -O chromedriver.zip \
         "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"
fi

# Check final download
if [ ! -f "chromedriver.zip" ] || [ ! -s "chromedriver.zip" ]; then
    echo "❌ ChromeDriver download failed"
    echo "🔗 Manual download needed from: https://chromedriver.chromium.org/"
    exit 1
fi

echo "✅ ChromeDriver downloaded successfully"

# Install ChromeDriver
echo "📦 Installing ChromeDriver..."

# Extract ChromeDriver
unzip -o chromedriver.zip
if [ -f "chromedriver" ]; then
    sudo mv chromedriver /usr/local/bin/
    sudo chmod +x /usr/local/bin/chromedriver
    echo "✅ ChromeDriver installed to /usr/local/bin/chromedriver"
else
    echo "❌ ChromeDriver extraction failed"
    exit 1
fi

# Clean up
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

echo ""
echo "🎉 ChromeDriver updated successfully!"
echo "===================================="
echo "✅ Chrome: $(google-chrome --version 2>/dev/null || echo 'Version check failed')"
echo "✅ ChromeDriver: $(chromedriver --version 2>/dev/null || echo 'Version check failed')"
echo ""
echo "🧪 Now test your setup:"
echo "   python3 test_chrome_ec2.py"
echo ""
echo "📝 Note: ChromeDriver $CHROMEDRIVER_VERSION should be compatible with Chrome 140"
