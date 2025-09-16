#!/bin/bash
#
# Simple Chrome Installation for Amazon Linux 3
# More reliable approach with better error handling
#

set -e  # Exit on any error

echo "🌐 Simple Chrome Installation for Amazon Linux 3"
echo "================================================"

# Update system first
echo "📦 Updating system packages..."
sudo dnf update -y

# Install essential dependencies
echo "📚 Installing dependencies..."
sudo dnf install -y \
    wget \
    curl \
    unzip \
    which \
    lsof

# Download Chrome directly
echo "⬇️ Downloading Chrome..."
cd /tmp
rm -f google-chrome-stable_current_x86_64.rpm
wget --no-check-certificate -O google-chrome-stable_current_x86_64.rpm \
    https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm

# Check if download was successful
if [ ! -f "google-chrome-stable_current_x86_64.rpm" ]; then
    echo "❌ Chrome download failed"
    exit 1
fi

echo "✅ Chrome downloaded successfully"

# Install Chrome with all dependencies
echo "📦 Installing Chrome..."
sudo dnf install -y google-chrome-stable_current_x86_64.rpm

# Clean up
rm -f google-chrome-stable_current_x86_64.rpm

# Find Chrome installation
echo "🔍 Locating Chrome installation..."
CHROME_PATH=""

# Check common locations
if [ -f "/usr/bin/google-chrome" ]; then
    CHROME_PATH="/usr/bin/google-chrome"
elif [ -f "/usr/bin/google-chrome-stable" ]; then
    CHROME_PATH="/usr/bin/google-chrome-stable"
elif [ -f "/opt/google/chrome/google-chrome" ]; then
    CHROME_PATH="/opt/google/chrome/google-chrome"
fi

if [ -n "$CHROME_PATH" ]; then
    echo "✅ Chrome found at: $CHROME_PATH"
    
    # Create symlink for easier access
    if [ ! -f "/usr/local/bin/google-chrome" ]; then
        sudo ln -sf "$CHROME_PATH" /usr/local/bin/google-chrome
        echo "✅ Created symlink: /usr/local/bin/google-chrome"
    fi
    
    # Test Chrome
    echo "🧪 Testing Chrome..."
    if "$CHROME_PATH" --version; then
        echo "✅ Chrome is working!"
    else
        echo "❌ Chrome test failed"
    fi
else
    echo "❌ Chrome not found after installation"
    exit 1
fi

# Install ChromeDriver
echo "🚗 Installing ChromeDriver..."

# Get Chrome version
CHROME_VERSION=$("$CHROME_PATH" --version | awk '{print $3}' | cut -d. -f1)
echo "Chrome version: $CHROME_VERSION"

# Get ChromeDriver version
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}")
echo "ChromeDriver version: $CHROMEDRIVER_VERSION"

# Download ChromeDriver
wget -O /tmp/chromedriver.zip \
    "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"

# Install ChromeDriver
sudo unzip -o /tmp/chromedriver.zip -d /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
rm -f /tmp/chromedriver.zip

# Test ChromeDriver
echo "🧪 Testing ChromeDriver..."
if chromedriver --version; then
    echo "✅ ChromeDriver is working!"
else
    echo "❌ ChromeDriver test failed"
fi

# Final test - headless Chrome
echo "🧪 Testing headless Chrome..."
if google-chrome --headless --no-sandbox --disable-dev-shm-usage --disable-gpu --version; then
    echo "✅ Headless Chrome is working!"
else
    echo "❌ Headless Chrome test failed"
fi

echo ""
echo "🎉 Installation completed!"
echo "=========================="
echo "Chrome: $(google-chrome --version)"
echo "ChromeDriver: $(chromedriver --version)"
echo ""
echo "🧪 Test with: python3 test_chrome_ec2.py"
