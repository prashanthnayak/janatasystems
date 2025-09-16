#!/bin/bash
#
# Install Chrome and ChromeDriver on Amazon Linux 3
# Quick installation for scraping functionality
#

set -e  # Exit on any error

echo "🌐 Installing Chrome and ChromeDriver on Amazon Linux 3"
echo "====================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're on Amazon Linux
if ! grep -q "Amazon Linux" /etc/os-release 2>/dev/null; then
    log_warning "This script is optimized for Amazon Linux 3"
fi

# Install minimal dependencies for Chrome
log_info "Installing minimal Chrome dependencies..."
sudo dnf install -y \
    wget \
    unzip \
    curl \
    gtk3 \
    nss \
    alsa-lib \
    liberation-fonts \
    xdg-utils \
    at-spi2-atk \
    at-spi2-core \
    cups-libs \
    libdrm \
    libxkbcommon \
    mesa-libgbm

log_success "Dependencies installed"

# Install Google Chrome
log_info "Downloading and installing Google Chrome..."
cd /tmp

# Download Chrome RPM
wget -O google-chrome-stable.rpm https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm

# Install Chrome with dependency resolution
sudo dnf install -y google-chrome-stable.rpm

# Clean up
rm -f google-chrome-stable.rpm

log_success "Google Chrome installed"

# Install ChromeDriver
log_info "Installing ChromeDriver..."

# Get Chrome version
if command -v google-chrome &> /dev/null; then
    CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d. -f1)
    log_info "Chrome version: $CHROME_VERSION"
    
    # Get matching ChromeDriver version
    CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}")
    log_info "ChromeDriver version: $CHROMEDRIVER_VERSION"
    
    # Download and install ChromeDriver
    wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"
    sudo unzip /tmp/chromedriver.zip -d /usr/local/bin/
    sudo chmod +x /usr/local/bin/chromedriver
    rm /tmp/chromedriver.zip
    
    log_success "ChromeDriver installed to /usr/local/bin/chromedriver"
else
    log_error "Chrome installation failed - cannot detect version"
    exit 1
fi

# Test the installation
log_info "Testing Chrome installation..."

# Test Chrome
if command -v google-chrome &> /dev/null; then
    CHROME_VER=$(google-chrome --version)
    log_success "Chrome: $CHROME_VER"
else
    log_error "Chrome not found after installation"
    exit 1
fi

# Test ChromeDriver
if command -v chromedriver &> /dev/null; then
    CHROMEDRIVER_VER=$(chromedriver --version)
    log_success "ChromeDriver: $CHROMEDRIVER_VER"
else
    log_error "ChromeDriver not found after installation"
    exit 1
fi

# Test headless Chrome
log_info "Testing headless Chrome functionality..."
if google-chrome --headless --no-sandbox --disable-dev-shm-usage --disable-gpu --dump-dom https://www.google.com > /dev/null 2>&1; then
    log_success "Headless Chrome test passed"
else
    log_warning "Headless Chrome test failed, but Chrome is installed"
fi

echo ""
log_success "🎉 Chrome and ChromeDriver installation completed!"
echo ""
echo "📋 What was installed:"
echo "   ✅ Google Chrome (latest stable)"
echo "   ✅ ChromeDriver (matching version)"
echo "   ✅ Required system dependencies"
echo ""
echo "🧪 Test your installation:"
echo "   python3 test_chrome_ec2.py"
echo ""
echo "🌐 Chrome location: $(which google-chrome)"
echo "🚗 ChromeDriver location: $(which chromedriver)"
echo ""
log_success "Your EC2 instance is now ready for web scraping!"
