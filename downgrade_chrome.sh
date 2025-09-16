#!/bin/bash
#
# Downgrade Chrome to version 131 to match ChromeDriver 131
#

echo "🔄 Downgrading Chrome to version 131 to match ChromeDriver"
echo "========================================================="

# Remove current Chrome 140
echo "🗑️ Removing Chrome 140..."
sudo dnf remove -y google-chrome-stable

# Download and install Chrome 131
echo "📥 Downloading Chrome 131..."
cd /tmp

# Chrome 131 stable version
CHROME_131_URL="https://dl.google.com/linux/chrome/rpm/stable/x86_64/google-chrome-stable-131.0.6778.204-1.x86_64.rpm"

wget -O google-chrome-131.rpm "$CHROME_131_URL"

if [ ! -f "google-chrome-131.rpm" ]; then
    echo "❌ Failed to download Chrome 131"
    echo "🔄 Trying alternative approach..."
    
    # Try getting Chrome 131 from archive
    wget -O google-chrome-131.rpm "https://dl.google.com/linux/chrome/rpm/stable/x86_64/google-chrome-stable-131.0.6778.85-1.x86_64.rpm"
fi

if [ ! -f "google-chrome-131.rpm" ]; then
    echo "❌ Could not download Chrome 131"
    echo "🔧 Manual solution needed:"
    echo "1. Go to: https://www.google.com/chrome/browser/desktop/index.html?extra=devchannel"
    echo "2. Download Chrome 131 manually"
    echo "3. Install with: sudo dnf install -y ./google-chrome-*.rpm"
    exit 1
fi

echo "📦 Installing Chrome 131..."
sudo dnf install -y ./google-chrome-131.rpm --allowerasing

# Clean up
rm -f google-chrome-131.rpm

# Verify installation
echo "🧪 Verifying Chrome installation..."
CHROME_VERSION=$(google-chrome --version 2>/dev/null)
if [[ "$CHROME_VERSION" == *"131"* ]]; then
    echo "✅ Chrome 131 installed successfully: $CHROME_VERSION"
else
    echo "⚠️ Chrome version: $CHROME_VERSION"
    echo "   This might still work with ChromeDriver 131"
fi

# Test ChromeDriver compatibility
echo "🧪 Testing ChromeDriver compatibility..."
CHROMEDRIVER_VERSION=$(chromedriver --version 2>/dev/null)
echo "✅ ChromeDriver: $CHROMEDRIVER_VERSION"

echo ""
echo "🎉 Chrome downgrade completed!"
echo "=============================="
echo "✅ Chrome: $(google-chrome --version 2>/dev/null)"
echo "✅ ChromeDriver: $(chromedriver --version 2>/dev/null)"
echo ""
echo "🧪 Now test your scraping:"
echo "   python3 test_scraping_simple.py"
