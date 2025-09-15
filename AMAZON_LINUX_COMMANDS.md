# 🚀 Amazon Linux 3 - Manual Installation Commands

## 📦 System Update & Basic Packages
```bash
# Update system
sudo dnf update -y

# Install Python 3 and development tools
sudo dnf install -y python3 python3-pip python3-devel python3-venv

# Install build tools
sudo dnf install -y gcc gcc-c++ make openssl-devel libffi-devel
```

## 🗄️ PostgreSQL Installation
```bash
# Install PostgreSQL 15
sudo dnf install -y postgresql15-server postgresql15 postgresql15-contrib postgresql15-devel

# Initialize and start PostgreSQL
sudo postgresql-setup --initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres createuser -s $(whoami)
sudo -u postgres psql -c "ALTER USER $(whoami) PASSWORD 'secure_password_123';"
sudo -u postgres createdb -O $(whoami) legal_management
```

## 🐍 Python Packages
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install packages
pip install selenium==4.20.0
pip install pillow
pip install transformers
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install flask==2.3.3 flask-cors==4.0.0
pip install psycopg2-binary==2.9.7
pip install requests python-dateutil beautifulsoup4 lxml
```

## 🌐 Chrome & ChromeDriver
```bash
# Install Chrome dependencies
sudo dnf install -y \
    xorg-x11-server-Xvfb \
    gtk3-devel \
    nss-devel \
    xorg-x11-xauth \
    dbus-glib-devel \
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
    gtk3 \
    libdrm \
    libxkbcommon \
    libxshmfence \
    mesa-libgbm

# Download and install Chrome
cd /tmp
wget -O google-chrome-stable.rpm https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
sudo dnf install -y google-chrome-stable.rpm
rm google-chrome-stable.rpm

# Install ChromeDriver
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d. -f1)
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}")
wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"
sudo unzip /tmp/chromedriver.zip -d /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
rm /tmp/chromedriver.zip
```

## 🔥 Firewall Configuration
```bash
# Start and enable firewalld
sudo systemctl start firewalld
sudo systemctl enable firewalld

# Add ports
sudo firewall-cmd --permanent --add-port=22/tcp      # SSH
sudo firewall-cmd --permanent --add-port=5002/tcp    # API
sudo firewall-cmd --permanent --add-port=8000/tcp    # Web
sudo firewall-cmd --permanent --add-port=5432/tcp    # PostgreSQL
sudo firewall-cmd --reload

# Check status
sudo firewall-cmd --list-all
```

## 🔧 Service Management
```bash
# Create systemd service
sudo tee /etc/systemd/system/legal-api.service > /dev/null <<EOF
[Unit]
Description=Legal Management API
After=network.target postgresql.service

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=/home/$(whoami)/legal_management
Environment=PATH=/home/$(whoami)/legal_management/venv/bin
Environment=DISPLAY=:99
ExecStart=/home/$(whoami)/legal_management/venv/bin/python legal_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload and start service
sudo systemctl daemon-reload
sudo systemctl start legal-api
sudo systemctl enable legal-api
```

## 🧪 Testing Commands
```bash
# Test Python packages
python3 -c "
import selenium, PIL, transformers, torch, torchvision
print('✅ All packages working')
print(f'Selenium: {selenium.__version__}')
print(f'PyTorch: {torch.__version__}')
"

# Test Chrome and ChromeDriver
google-chrome --version
chromedriver --version

# Test database connection
python3 -c "
import psycopg2
conn = psycopg2.connect(
    host='localhost',
    database='legal_management',
    user='$(whoami)',
    password='secure_password_123'
)
print('✅ Database connection OK')
conn.close()
"

# Test API
curl http://localhost:5002/api/health
```

## 📊 Monitoring Commands
```bash
# Check service status
sudo systemctl status legal-api

# View logs
journalctl -u legal-api -f

# Check network ports
sudo ss -tulpn | grep -E ':(5002|5432|8000)'

# System resources
free -h
df -h
top -bn1 | grep "Cpu(s)"
```

## 🔄 Package Manager Differences

| Ubuntu/Debian | Amazon Linux 3 | Purpose |
|---------------|----------------|---------|
| `apt update` | `dnf update` | Update packages |
| `apt install` | `dnf install` | Install packages |
| `apt search` | `dnf search` | Search packages |
| `ufw` | `firewalld` | Firewall |
| `systemctl` | `systemctl` | Services (same) |

## 🚨 Troubleshooting

### Chrome Issues:
```bash
# If Chrome won't start
export DISPLAY=:99
google-chrome --headless --no-sandbox --disable-dev-shm-usage --version
```

### Database Issues:
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check database exists
sudo -u postgres psql -l | grep legal_management

# Reset PostgreSQL if needed
sudo systemctl restart postgresql
```

### Permission Issues:
```bash
# Fix file permissions
chmod +x *.sh
chown -R $USER:$USER /home/$USER/legal_management/
```

### Service Issues:
```bash
# Check service logs
journalctl -u legal-api --no-pager -n 50

# Restart service
sudo systemctl restart legal-api
```

## 🎯 Quick Setup Summary
```bash
# 1. Update system
sudo dnf update -y

# 2. Run the automated script
chmod +x install_scraping_deps_amazon_linux.sh
./install_scraping_deps_amazon_linux.sh

# 3. Or run the full installation
chmod +x install_ec2_amazon_linux.sh
./install_ec2_amazon_linux.sh
```

This covers all the Amazon Linux 3 specific commands and differences! 🚀
