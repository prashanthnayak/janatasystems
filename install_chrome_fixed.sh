#!/bin/bash
#
# Fixed Chrome Installation for Amazon Linux 3
# Handles curl conflicts and other common issues
#

set -e  # Exit on any error

echo "🌐 Fixed Chrome Installation for Amazon Linux 3"
echo "==============================================="

# Function to handle curl conflicts
fix_curl_conflict() {
    echo "🔧 Handling curl package conflicts..."
    
    # Check if curl-minimal is installed
    if rpm -qa | grep -q curl-minimal; then
        echo "ℹ️ curl-minimal detected, skipping curl installation"
        # curl-minimal provides basic curl functionality, which is sufficient
        return 0
    fi
    
    # If no curl at all, install curl-minimal (lighter and less conflicts)
    if ! command -v curl &> /dev/null; then
        echo "📦 Installing curl-minimal..."
        sudo dnf install -y curl-minimal
    fi
}

# Fix curl conflicts first
fix_curl_conflict

# Install essential dependencies (without curl to avoid conflicts)
echo "📚 Installing dependencies..."
sudo dnf install -y \
    wget \
    unzip \
    which \
    lsof \
    gtk3 \
    nss \
    alsa-lib \
    liberation-fonts \
    xdg-utils

# Download Chrome directly using wget (more reliable than curl)
echo "⬇️ Downloading Chrome..."
cd /tmp
rm -f google-chrome-stable_current_x86_64.rpm

# Use wget instead of curl to avoid conflicts
wget --no-check-certificate --timeout=30 --tries=3 \
    -O google-chrome-stable_current_x86_64.rpm \
    https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm

# Verify download
if [ ! -f "google-chrome-stable_current_x86_64.rpm" ] || [ ! -s "google-chrome-stable_current_x86_64.rpm" ]; then
    echo "❌ Chrome download failed or file is empty"
    echo "🔄 Trying alternative download method..."
    
    # Alternative download using a different approach
    wget --no-check-certificate --user-agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
         -O google-chrome-stable_current_x86_64.rpm \
         https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
fi

if [ ! -f "google-chrome-stable_current_x86_64.rpm" ] || [ ! -s "google-chrome-stable_current_x86_64.rpm" ]; then
    echo "❌ Chrome download failed completely"
    exit 1
fi

echo "✅ Chrome downloaded successfully ($(du -h google-chrome-stable_current_x86_64.rpm | cut -f1))"

# Install Chrome with dependency resolution
echo "📦 Installing Chrome..."
sudo dnf install -y ./google-chrome-stable_current_x86_64.rpm

# Clean up
rm -f google-chrome-stable_current_x86_64.rpm

# Find and verify Chrome installation
echo "🔍 Verifying Chrome installation..."
CHROME_PATH=""

# Check common locations
CHROME_LOCATIONS=(
    "/usr/bin/google-chrome"
    "/usr/bin/google-chrome-stable"
    "/opt/google/chrome/google-chrome"
)

for location in "${CHROME_LOCATIONS[@]}"; do
    if [ -f "$location" ] && [ -x "$location" ]; then
        CHROME_PATH="$location"
        echo "✅ Chrome found at: $CHROME_PATH"
        break
    fi
done

if [ -z "$CHROME_PATH" ]; then
    echo "❌ Chrome not found after installation"
    echo "🔍 Searching for Chrome in all locations..."
    find /usr /opt -name "*chrome*" -type f 2>/dev/null | head -10
    exit 1
fi

# Create symlink for easier access
if [ "$CHROME_PATH" != "/usr/local/bin/google-chrome" ]; then
    sudo ln -sf "$CHROME_PATH" /usr/local/bin/google-chrome
    echo "✅ Created symlink: /usr/local/bin/google-chrome -> $CHROME_PATH"
fi

# Test Chrome
echo "🧪 Testing Chrome..."
if "$CHROME_PATH" --version 2>/dev/null; then
    CHROME_VERSION_OUTPUT=$("$CHROME_PATH" --version)
    echo "✅ Chrome is working: $CHROME_VERSION_OUTPUT"
else
    echo "❌ Chrome test failed, checking dependencies..."
    ldd "$CHROME_PATH" | grep "not found" || echo "All dependencies satisfied"
    exit 1
fi

# Install ChromeDriver
echo "🚗 Installing ChromeDriver..."

# Extract Chrome version number
CHROME_VERSION=$("$CHROME_PATH" --version | grep -oP '\d+\.\d+\.\d+\.\d+' | head -1)
CHROME_MAJOR_VERSION=$(echo "$CHROME_VERSION" | cut -d. -f1)
echo "Chrome version: $CHROME_VERSION (major: $CHROME_MAJOR_VERSION)"

# Get ChromeDriver version using wget instead of curl
echo "🔍 Getting ChromeDriver version..."
CHROMEDRIVER_VERSION=""

# Try to get ChromeDriver version using wget
if command -v curl &> /dev/null; then
    CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAJOR_VERSION}" 2>/dev/null || echo "")
fi

# Fallback to wget if curl failed
if [ -z "$CHROMEDRIVER_VERSION" ]; then
    CHROMEDRIVER_VERSION=$(wget -qO- "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAJOR_VERSION}" 2>/dev/null || echo "")
fi

# If still no version, use the Chrome version
if [ -z "$CHROMEDRIVER_VERSION" ]; then
    CHROMEDRIVER_VERSION="$CHROME_VERSION"
fi

echo "ChromeDriver version: $CHROMEDRIVER_VERSION"

# Download ChromeDriver
echo "⬇️ Downloading ChromeDriver..."
wget --no-check-certificate --timeout=30 \
     -O /tmp/chromedriver.zip \
     "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"

if [ ! -f "/tmp/chromedriver.zip" ] || [ ! -s "/tmp/chromedriver.zip" ]; then
    echo "❌ ChromeDriver download failed"
    exit 1
fi

# Install ChromeDriver
sudo unzip -o /tmp/chromedriver.zip -d /usr/local/bin/
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

# Final comprehensive test
echo "🧪 Testing headless Chrome..."
if google-chrome --headless --no-sandbox --disable-dev-shm-usage --disable-gpu --dump-dom data:text/html,test >/dev/null 2>&1; then
    echo "✅ Headless Chrome is working perfectly!"
else
    echo "⚠️ Headless Chrome test had issues, but Chrome is installed"
    echo "This might still work for scraping - try running your test script"
fi

echo ""
echo "🎉 Installation completed successfully!"
echo "====================================="
echo "✅ Chrome: $("$CHROME_PATH" --version)"
echo "✅ ChromeDriver: $(chromedriver --version)"
echo "✅ Location: $CHROME_PATH"
echo "✅ Symlink: /usr/local/bin/google-chrome"
echo ""
echo "🧪 Next steps:"
echo "1. Test with: python3 test_chrome_ec2.py"
echo "2. If that works, your scraping should work!"
echo ""
echo "🔧 If you still get 'Chrome not found':"
echo "   export PATH=\$PATH:/usr/local/bin"
echo "   source ~/.bashrc"
