# 🔧 Manual Installation Guide - Scraping Dependencies

## 🐍 Python Packages

### Install Python packages:
```bash
# Upgrade pip first
python3 -m pip install --upgrade pip

# Install Selenium
python3 -m pip install selenium==4.20.0

# Install image processing
python3 -m pip install pillow

# Install AI/ML packages
python3 -m pip install transformers

# Install PyTorch (choose based on your system)
# For CPU only (recommended for most users):
python3 -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# For GPU support (if you have NVIDIA GPU):
# python3 -m pip install torch torchvision torchaudio
```

## 🌐 Google Chrome Installation

### Ubuntu/Debian:
```bash
# Add Google's signing key
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -

# Add Chrome repository
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list

# Update and install
sudo apt update
sudo apt install -y google-chrome-stable
```

### macOS:
```bash
# Using Homebrew
brew install --cask google-chrome

# Or download manually from: https://www.google.com/chrome/
```

### CentOS/RHEL:
```bash
# Add Chrome repository
sudo tee /etc/yum.repos.d/google-chrome.repo <<EOF
[google-chrome]
name=google-chrome
baseurl=http://dl.google.com/linux/chrome/rpm/stable/x86_64
enabled=1
gpgcheck=1
gpgkey=https://dl.google.com/linux/linux_signing_key.pub
EOF

# Install Chrome
sudo yum install -y google-chrome-stable
```

## 🚗 ChromeDriver Installation

### Ubuntu/Debian:
```bash
# Get Chrome version
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d. -f1)

# Get matching ChromeDriver version
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}")

# Download and install ChromeDriver
wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"
sudo unzip /tmp/chromedriver.zip -d /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
rm /tmp/chromedriver.zip
```

### macOS:
```bash
# Using Homebrew
brew install chromedriver

# Or manual installation:
# 1. Check Chrome version: /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version
# 2. Download matching ChromeDriver from: https://chromedriver.chromium.org/downloads
# 3. Extract and move to /usr/local/bin/
```

### CentOS/RHEL:
```bash
# Same as Ubuntu, but use appropriate paths
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d. -f1)
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}")
wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"
sudo unzip /tmp/chromedriver.zip -d /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
rm /tmp/chromedriver.zip
```

## 📦 Additional System Dependencies (Linux only)

### Ubuntu/Debian:
```bash
sudo apt install -y \
    libnss3-dev \
    libgdk-pixbuf2.0-dev \
    libgtk-3-dev \
    libxss1 \
    libasound2 \
    libxtst6 \
    libxrandr2 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libcairo-gobject2 \
    libgtk-3-0 \
    libgdk-pixbuf2.0-0
```

### CentOS/RHEL:
```bash
sudo yum install -y \
    nss \
    gdk-pixbuf2 \
    gtk3 \
    libXss \
    alsa-lib \
    libXtst \
    libXrandr
```

## 🧪 Test Installation

### Quick Test:
```bash
# Test Python packages
python3 -c "
import selenium
import PIL
import transformers
import torch
import torchvision
print('✅ All packages imported successfully')
"

# Test Chrome
google-chrome --version

# Test ChromeDriver
chromedriver --version
```

### Full Test Script:
```python
#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Setup Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

try:
    # Create driver
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://www.google.com")
    print(f"✅ Success! Page title: {driver.title}")
    driver.quit()
except Exception as e:
    print(f"❌ Error: {e}")
```

## 🔧 Troubleshooting

### Common Issues:

#### ChromeDriver not found:
```bash
# Make sure ChromeDriver is in PATH
which chromedriver
# Should return: /usr/local/bin/chromedriver

# If not found, add to PATH:
export PATH=$PATH:/usr/local/bin
```

#### Chrome version mismatch:
```bash
# Check versions match
google-chrome --version
chromedriver --version

# If mismatch, reinstall ChromeDriver with correct version
```

#### Permission denied:
```bash
# Fix ChromeDriver permissions
sudo chmod +x /usr/local/bin/chromedriver
```

#### PyTorch installation issues:
```bash
# For older systems, use CPU-only version
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

#### Transformers cache issues:
```bash
# Clear transformers cache if needed
rm -rf ~/.cache/huggingface/
```

## 📋 Version Compatibility

| Package | Version | Notes |
|---------|---------|-------|
| selenium | 4.20.0 | Exact version required |
| pillow | Latest | Image processing |
| transformers | Latest | Hugging Face transformers |
| torch | Latest | PyTorch for AI models |
| torchvision | Latest | Computer vision utilities |
| Chrome | 120+ | Modern version recommended |
| ChromeDriver | Match Chrome | Must match Chrome version |

## 🎯 Final Verification

Run this command to verify everything is working:
```bash
python3 -c "
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import PIL, transformers, torch, torchvision

options = Options()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)
driver.get('https://httpbin.org/json')
print('🎉 All dependencies working correctly!')
driver.quit()
"
```

If this runs without errors, your scraping environment is ready! 🚀
