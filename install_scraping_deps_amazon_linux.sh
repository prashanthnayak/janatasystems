#!/bin/bash
#
# Install Scraping Dependencies - Amazon Linux 3
# For Legal Management System Web Scraping
#

set -e  # Exit on any error

echo "🔧 Installing Scraping Dependencies on Amazon Linux 3"
echo "===================================================="

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

# Verify we're on Amazon Linux
if ! grep -q "Amazon Linux" /etc/os-release; then
    log_error "This script is for Amazon Linux 3. Use install_scraping_deps.sh for other systems."
    exit 1
fi

log_info "Detected Amazon Linux system"

# Update package manager
log_info "Updating DNF package manager..."
sudo dnf update -y
log_success "Package manager updated"

# Install Python 3 and pip if not already installed
log_info "Installing Python 3 and pip..."
sudo dnf install -y python3 python3-pip python3-devel
log_success "Python 3 and pip installed"

# Install system dependencies for Chrome and scraping
log_info "Installing system dependencies..."
sudo dnf install -y \
    wget \
    unzip \
    curl \
    xorg-x11-server-Xvfb \
    gtk3-devel \
    nss-devel \
    xorg-x11-xauth \
    dbus-glib-devel \
    dbus-glib \
    alsa-lib \
    libXtst \
    libXrandr \
    libXScrnSaver \
    libXcomposite \
    libXcursor \
    libXdamage \
    libXext \
    libXfixes \
    libXi \
    libXrender \
    liberation-fonts \
    liberation-fonts-common \
    xdg-utils \
    at-spi2-atk \
    at-spi2-core \
    cups-libs \
    drpm \
    gtk3 \
    libdrm \
    libxkbcommon \
    libxshmfence \
    mesa-libgbm

log_success "System dependencies installed"

# Install Python packages
log_info "Installing Python packages..."

# Upgrade pip first
python3 -m pip install --upgrade pip --user

# Install packages one by one with specific versions
log_info "Installing Selenium 4.20.0..."
python3 -m pip install selenium==4.20.0 --user
log_success "Selenium installed"

log_info "Installing Pillow (PIL)..."
python3 -m pip install pillow --user
log_success "Pillow installed"

log_info "Installing Transformers..."
python3 -m pip install transformers --user
log_success "Transformers installed"

log_info "Installing PyTorch (CPU version for Amazon Linux)..."
python3 -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu --user
log_success "PyTorch installed"

# Install additional Python packages that might be needed
log_info "Installing additional Python packages..."
python3 -m pip install beautifulsoup4 lxml requests --user
log_success "Additional packages installed"

# Install Google Chrome
log_info "Installing Google Chrome..."

# Download Chrome RPM
cd /tmp
wget -O google-chrome-stable.rpm https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm

# Install Chrome
sudo dnf install -y google-chrome-stable.rpm

# Clean up
rm -f google-chrome-stable.rpm

log_success "Google Chrome installed"

# Install ChromeDriver
log_info "Installing ChromeDriver..."

# Get Chrome version
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

# Add user's local bin to PATH if not already there
if ! echo $PATH | grep -q "$HOME/.local/bin"; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    export PATH="$HOME/.local/bin:$PATH"
    log_info "Added ~/.local/bin to PATH"
fi

# Test installation
log_info "Testing installation..."

# Test Python packages
python3 -c "
import selenium
import PIL
import transformers
import torch
import torchvision
print('✅ All Python packages imported successfully')
print(f'Selenium version: {selenium.__version__}')
print(f'PIL version: {PIL.__version__}')
print(f'Transformers version: {transformers.__version__}')
print(f'PyTorch version: {torch.__version__}')
print(f'TorchVision version: {torchvision.__version__}')
"

# Test ChromeDriver
if command -v chromedriver &> /dev/null; then
    CHROMEDRIVER_VER=$(chromedriver --version)
    log_success "ChromeDriver: $CHROMEDRIVER_VER"
else
    log_error "ChromeDriver not found in PATH"
    exit 1
fi

# Test Chrome
if command -v google-chrome &> /dev/null; then
    CHROME_VER=$(google-chrome --version)
    log_success "Chrome: $CHROME_VER"
else
    log_error "Google Chrome not found"
    exit 1
fi

# Create test script specifically for Amazon Linux
log_info "Creating test script for Amazon Linux..."
cat > test_scraping_amazon.py << 'EOF'
#!/usr/bin/env python3
"""
Test script for scraping dependencies on Amazon Linux 3
"""

def test_selenium():
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        
        # Setup Chrome options for headless operation on Amazon Linux
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-features=TranslateUI")
        chrome_options.add_argument("--disable-ipc-flooding-protection")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Create service
        service = Service('/usr/local/bin/chromedriver')
        
        # Create driver
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get("https://www.google.com")
        title = driver.title
        driver.quit()
        
        print(f"✅ Selenium test passed - Page title: {title}")
        return True
    except Exception as e:
        print(f"❌ Selenium test failed: {e}")
        return False

def test_ai_packages():
    try:
        import torch
        from transformers import pipeline
        from PIL import Image
        import numpy as np
        
        # Test PyTorch
        tensor = torch.tensor([1, 2, 3])
        print(f"✅ PyTorch test passed - Tensor: {tensor}")
        
        # Test PIL
        img = Image.new('RGB', (100, 100), color='red')
        print(f"✅ PIL test passed - Image size: {img.size}")
        
        print("✅ All AI packages working")
        return True
    except Exception as e:
        print(f"❌ AI packages test failed: {e}")
        return False

def test_system_info():
    import platform
    import os
    
    print(f"🖥️  System: {platform.system()} {platform.release()}")
    print(f"🐍 Python: {platform.python_version()}")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"👤 User: {os.getenv('USER', 'unknown')}")
    
    # Check if running on EC2
    try:
        import urllib.request
        response = urllib.request.urlopen('http://169.254.169.254/latest/meta-data/instance-id', timeout=2)
        instance_id = response.read().decode()
        print(f"☁️  EC2 Instance ID: {instance_id}")
    except:
        print("💻 Not running on EC2")

if __name__ == "__main__":
    print("🧪 Testing scraping dependencies on Amazon Linux 3...")
    print("=" * 55)
    
    test_system_info()
    print()
    
    selenium_ok = test_selenium()
    ai_ok = test_ai_packages()
    
    if selenium_ok and ai_ok:
        print("\n🎉 All tests passed! Scraping functionality is ready on Amazon Linux 3.")
    else:
        print("\n❌ Some tests failed. Please check the installation.")
EOF

chmod +x test_scraping_amazon.py
log_success "Test script created: test_scraping_amazon.py"

# Create environment setup script
log_info "Creating environment setup script..."
cat > setup_scraping_env.sh << 'EOF'
#!/bin/bash
# Environment setup for scraping on Amazon Linux 3

# Add local bin to PATH
export PATH="$HOME/.local/bin:$PATH"

# Set display for headless operation
export DISPLAY=:99

# Chrome/ChromeDriver paths
export CHROME_BIN=/usr/bin/google-chrome
export CHROMEDRIVER_PATH=/usr/local/bin/chromedriver

# Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo "🔧 Environment configured for scraping on Amazon Linux 3"
echo "Chrome: $CHROME_BIN"
echo "ChromeDriver: $CHROMEDRIVER_PATH"
echo "Python Path: $PYTHONPATH"
EOF

chmod +x setup_scraping_env.sh
log_success "Environment setup script created: setup_scraping_env.sh"

echo ""
log_success "🎉 Installation completed successfully on Amazon Linux 3!"
echo ""
echo "📋 Installed packages:"
echo "   ✅ selenium==4.20.0"
echo "   ✅ pillow"
echo "   ✅ transformers"
echo "   ✅ torch (CPU version)"
echo "   ✅ torchvision"
echo "   ✅ Google Chrome"
echo "   ✅ ChromeDriver"
echo ""
echo "🔧 Setup commands:"
echo "   source setup_scraping_env.sh  # Setup environment"
echo "   python3 test_scraping_amazon.py  # Test installation"
echo ""
echo "💡 Important notes for Amazon Linux 3:"
echo "   - Packages installed with --user flag"
echo "   - Chrome runs in headless mode"
echo "   - Environment variables configured"
echo "   - All dependencies optimized for EC2"
echo ""
echo "🚀 Your Amazon Linux 3 system is now ready for web scraping!"

# Run the test automatically
log_info "Running automatic test..."
source setup_scraping_env.sh
python3 test_scraping_amazon.py
