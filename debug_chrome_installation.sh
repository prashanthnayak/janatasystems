#!/bin/bash
#
# Debug Chrome Installation on Amazon Linux 3
# This script helps diagnose Chrome installation issues
#

echo "🔍 Chrome Installation Diagnostic"
echo "=================================="

# Check if Chrome binary exists in common locations
echo "📍 Checking Chrome binary locations..."

CHROME_LOCATIONS=(
    "/usr/bin/google-chrome"
    "/usr/bin/google-chrome-stable"
    "/opt/google/chrome/google-chrome"
    "/usr/local/bin/google-chrome"
)

CHROME_FOUND=""
for location in "${CHROME_LOCATIONS[@]}"; do
    if [ -f "$location" ]; then
        echo "✅ Found Chrome at: $location"
        CHROME_FOUND="$location"
        break
    else
        echo "❌ Not found: $location"
    fi
done

# Check if Chrome is in PATH
echo ""
echo "📍 Checking PATH..."
if command -v google-chrome &> /dev/null; then
    echo "✅ google-chrome found in PATH: $(which google-chrome)"
elif command -v google-chrome-stable &> /dev/null; then
    echo "✅ google-chrome-stable found in PATH: $(which google-chrome-stable)"
else
    echo "❌ Chrome not found in PATH"
fi

# Check installed packages
echo ""
echo "📦 Checking installed Chrome packages..."
if dnf list installed | grep -i chrome; then
    echo "✅ Chrome package is installed"
else
    echo "❌ No Chrome package found"
fi

# Check if Chrome RPM was downloaded/installed
echo ""
echo "📥 Checking Chrome installation status..."
if rpm -qa | grep -i chrome; then
    echo "✅ Chrome RPM is installed"
else
    echo "❌ Chrome RPM not found"
fi

# Try to run Chrome directly if found
if [ -n "$CHROME_FOUND" ]; then
    echo ""
    echo "🧪 Testing Chrome directly..."
    if "$CHROME_FOUND" --version 2>/dev/null; then
        echo "✅ Chrome executable works"
    else
        echo "❌ Chrome executable failed"
        echo "Error details:"
        "$CHROME_FOUND" --version 2>&1 || true
    fi
fi

# Check system architecture
echo ""
echo "🏗️ System information..."
echo "Architecture: $(uname -m)"
echo "OS: $(cat /etc/os-release | grep PRETTY_NAME)"

# Check for missing dependencies
echo ""
echo "📚 Checking dependencies..."
DEPS=("gtk3" "nss" "alsa-lib" "liberation-fonts")
for dep in "${DEPS[@]}"; do
    if rpm -qa | grep -q "$dep"; then
        echo "✅ $dep installed"
    else
        echo "❌ $dep missing"
    fi
done

echo ""
echo "🔧 SUGGESTED FIXES:"
echo "==================="

if [ -z "$CHROME_FOUND" ]; then
    echo "1. Chrome is not installed. Run:"
    echo "   wget -O /tmp/chrome.rpm https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm"
    echo "   sudo dnf install -y /tmp/chrome.rpm"
    echo ""
fi

echo "2. If Chrome is installed but not in PATH, create a symlink:"
echo "   sudo ln -sf /usr/bin/google-chrome-stable /usr/local/bin/google-chrome"
echo ""

echo "3. Try running Chrome with full path:"
echo "   /usr/bin/google-chrome-stable --version"
echo ""

echo "4. Check Chrome dependencies:"
echo "   ldd /usr/bin/google-chrome-stable | grep 'not found'"
