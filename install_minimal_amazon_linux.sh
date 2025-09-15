#!/bin/bash
#
# Minimal Installation for Amazon Linux 3 - Core Packages Only
# This script installs only the essential packages that are guaranteed to exist
#

set -e  # Exit on any error

echo "🔧 Minimal Installation for Amazon Linux 3"
echo "==========================================="

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

# Update system
log_info "Updating system..."
sudo dnf update -y
log_success "System updated"

# Install core development tools
log_info "Installing core development tools..."
sudo dnf groupinstall -y "Development Tools"
sudo dnf install -y python3 python3-pip python3-devel
log_success "Development tools installed"

# Install minimal Chrome dependencies (only the essential ones)
log_info "Installing minimal Chrome dependencies..."
sudo dnf install -y \
    wget \
    unzip \
    curl \
    gtk3 \
    nss \
    alsa-lib \
    liberation-fonts \
    xdg-utils

log_success "Minimal dependencies installed"

# Install Python packages
log_info "Installing Python packages..."
python3 -m pip install --upgrade pip --user

# Install packages one by one to catch any failures
packages=("selenium==4.20.0" "pillow" "transformers" "requests" "beautifulsoup4")

for package in "${packages[@]}"; do
    log_info "Installing $package..."
    python3 -m pip install "$package" --user
    log_success "$package installed"
done

# Install PyTorch CPU version
log_info "Installing PyTorch (CPU version)..."
python3 -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu --user
log_success "PyTorch installed"

# Install Google Chrome
log_info "Installing Google Chrome..."
cd /tmp
wget -q -O google-chrome-stable.rpm https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm

# Install Chrome and ignore dependency issues
sudo dnf install -y google-chrome-stable.rpm --skip-broken || {
    log_warning "Chrome installation had some dependency issues, but may still work"
}

rm -f google-chrome-stable.rpm
log_success "Google Chrome installation attempted"

# Install ChromeDriver
log_info "Installing ChromeDriver..."
if command -v google-chrome &> /dev/null; then
    CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d. -f1)
    log_info "Chrome version: $CHROME_VERSION"
    
    CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}")
    log_info "ChromeDriver version: $CHROMEDRIVER_VERSION"
    
    wget -q -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"
    sudo unzip /tmp/chromedriver.zip -d /usr/local/bin/
    sudo chmod +x /usr/local/bin/chromedriver
    rm /tmp/chromedriver.zip
    
    log_success "ChromeDriver installed"
else
    log_error "Chrome not found, skipping ChromeDriver installation"
fi

# Add user's local bin to PATH
if ! echo $PATH | grep -q "$HOME/.local/bin"; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    export PATH="$HOME/.local/bin:$PATH"
    log_info "Added ~/.local/bin to PATH"
fi

# Create a simple test
log_info "Creating simple test..."
cat > test_minimal.py << 'EOF'
#!/usr/bin/env python3
import sys

def test_imports():
    try:
        import selenium
        print(f"✅ Selenium {selenium.__version__}")
    except ImportError as e:
        print(f"❌ Selenium: {e}")
        return False
    
    try:
        import PIL
        print(f"✅ PIL {PIL.__version__}")
    except ImportError as e:
        print(f"❌ PIL: {e}")
        return False
    
    try:
        import torch
        print(f"✅ PyTorch {torch.__version__}")
    except ImportError as e:
        print(f"❌ PyTorch: {e}")
        return False
    
    try:
        import requests
        print(f"✅ Requests {requests.__version__}")
    except ImportError as e:
        print(f"❌ Requests: {e}")
        return False
    
    return True

def test_chrome():
    import subprocess
    try:
        result = subprocess.run(['google-chrome', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Chrome: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Chrome test failed: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ Chrome not found")
        return False

def test_chromedriver():
    import subprocess
    try:
        result = subprocess.run(['chromedriver', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ ChromeDriver: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ ChromeDriver test failed: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ ChromeDriver not found")
        return False

if __name__ == "__main__":
    print("🧪 Testing minimal installation...")
    print("=" * 40)
    
    imports_ok = test_imports()
    chrome_ok = test_chrome()
    chromedriver_ok = test_chromedriver()
    
    if imports_ok and chrome_ok and chromedriver_ok:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n⚠️ Some components may not be working correctly")
        sys.exit(1)
EOF

chmod +x test_minimal.py
log_success "Test script created: test_minimal.py"

echo ""
log_success "🎉 Minimal installation completed!"
echo ""
echo "📋 What was installed:"
echo "   ✅ Python 3 and pip"
echo "   ✅ Development tools"
echo "   ✅ Python packages (selenium, pillow, torch, etc.)"
echo "   ✅ Google Chrome (with minimal dependencies)"
echo "   ✅ ChromeDriver"
echo ""
echo "🧪 Test your installation:"
echo "   python3 test_minimal.py"
echo ""
echo "💡 If Chrome has issues, you can install additional dependencies manually:"
echo "   sudo dnf install -y gtk3-devel nss-devel xorg-x11-server-Xvfb"
echo ""

# Run the test
log_info "Running test..."
python3 test_minimal.py
