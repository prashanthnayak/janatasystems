#!/bin/bash
#
# Install Scraping Dependencies
# For Legal Management System Web Scraping
#

set -e  # Exit on any error

echo "🔧 Installing Scraping Dependencies for Legal Management System"
echo "=============================================================="

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

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    log_info "Detected Linux system"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="mac"
    log_info "Detected macOS system"
else
    log_error "Unsupported operating system: $OSTYPE"
    exit 1
fi

# Update package manager
if [[ "$OS" == "linux" ]]; then
    log_info "Updating package manager..."
    sudo apt update
    log_success "Package manager updated"
elif [[ "$OS" == "mac" ]]; then
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        log_info "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        log_success "Homebrew installed"
    else
        log_info "Updating Homebrew..."
        brew update
        log_success "Homebrew updated"
    fi
fi

# Install Python packages
log_info "Installing Python packages..."

# Upgrade pip first
python3 -m pip install --upgrade pip

# Install packages one by one with specific versions
log_info "Installing Selenium 4.20.0..."
python3 -m pip install selenium==4.20.0
log_success "Selenium installed"

log_info "Installing Pillow (PIL)..."
python3 -m pip install pillow
log_success "Pillow installed"

log_info "Installing Transformers..."
python3 -m pip install transformers
log_success "Transformers installed"

log_info "Installing PyTorch..."
if [[ "$OS" == "mac" ]]; then
    # For Mac, install CPU version
    python3 -m pip install torch torchvision torchaudio
else
    # For Linux, install CPU version
    python3 -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi
log_success "PyTorch installed"

# Install Chrome Browser
if [[ "$OS" == "linux" ]]; then
    log_info "Installing Google Chrome on Linux..."
    
    # Download and install Chrome
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
    sudo apt update
    sudo apt install -y google-chrome-stable
    
    log_success "Google Chrome installed"
    
elif [[ "$OS" == "mac" ]]; then
    log_info "Installing Google Chrome on macOS..."
    
    if ! command -v /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome &> /dev/null; then
        brew install --cask google-chrome
        log_success "Google Chrome installed"
    else
        log_warning "Google Chrome already installed"
    fi
fi

# Install ChromeDriver
log_info "Installing ChromeDriver..."

if [[ "$OS" == "linux" ]]; then
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
    
elif [[ "$OS" == "mac" ]]; then
    # Install ChromeDriver via Homebrew
    brew install chromedriver
    log_success "ChromeDriver installed"
fi

# Install additional system dependencies for Linux
if [[ "$OS" == "linux" ]]; then
    log_info "Installing additional system dependencies..."
    sudo apt install -y \
        libnss3-dev \
        libgdk-pixbuf2.0-dev \
        libgtk-3-dev \
        libxss1 \
        libasound2 \
        libxtst6 \
        libxrandr2 \
        libasound2 \
        libpangocairo-1.0-0 \
        libatk1.0-0 \
        libcairo-gobject2 \
        libgtk-3-0 \
        libgdk-pixbuf2.0-0
    log_success "System dependencies installed"
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
if [[ "$OS" == "linux" ]]; then
    if command -v google-chrome &> /dev/null; then
        CHROME_VER=$(google-chrome --version)
        log_success "Chrome: $CHROME_VER"
    else
        log_error "Google Chrome not found"
        exit 1
    fi
elif [[ "$OS" == "mac" ]]; then
    if [[ -f "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]]; then
        CHROME_VER=$("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --version)
        log_success "Chrome: $CHROME_VER"
    else
        log_error "Google Chrome not found"
        exit 1
    fi
fi

# Create test script
log_info "Creating test script..."
cat > test_scraping.py << 'EOF'
#!/usr/bin/env python3
"""
Test script for scraping dependencies
"""

def test_selenium():
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Create driver
        driver = webdriver.Chrome(options=chrome_options)
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

if __name__ == "__main__":
    print("🧪 Testing scraping dependencies...")
    print("=" * 40)
    
    selenium_ok = test_selenium()
    ai_ok = test_ai_packages()
    
    if selenium_ok and ai_ok:
        print("\n🎉 All tests passed! Scraping functionality is ready.")
    else:
        print("\n❌ Some tests failed. Please check the installation.")
EOF

chmod +x test_scraping.py
log_success "Test script created: test_scraping.py"

echo ""
log_success "🎉 Installation completed successfully!"
echo ""
echo "📋 Installed packages:"
echo "   ✅ selenium==4.20.0"
echo "   ✅ pillow"
echo "   ✅ transformers"
echo "   ✅ torch"
echo "   ✅ torchvision"
echo "   ✅ Google Chrome"
echo "   ✅ ChromeDriver"
echo ""
echo "🧪 Test your installation:"
echo "   python3 test_scraping.py"
echo ""
echo "🚀 Your system is now ready for web scraping!"

# Run the test automatically
log_info "Running automatic test..."
python3 test_scraping.py
