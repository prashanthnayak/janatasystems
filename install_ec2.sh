#!/bin/bash
#
# Legal Management System - EC2 Installation Script
# This script installs all dependencies and sets up the system on Ubuntu EC2
#
# Usage: chmod +x install_ec2.sh && ./install_ec2.sh
#

set -e  # Exit on any error

echo "🚀 Legal Management System - EC2 Installation"
echo "=============================================="

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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   log_error "This script should not be run as root"
   exit 1
fi

log_info "Starting installation process..."

# Update system packages
log_info "Updating system packages..."
sudo apt update && sudo apt upgrade -y
log_success "System packages updated"

# Install Python 3 and pip
log_info "Installing Python 3 and pip..."
sudo apt install -y python3 python3-pip python3-venv python3-dev
log_success "Python 3 and pip installed"

# Install PostgreSQL
log_info "Installing PostgreSQL..."
sudo apt install -y postgresql postgresql-contrib postgresql-client
log_success "PostgreSQL installed"

# Start and enable PostgreSQL
log_info "Starting PostgreSQL service..."
sudo systemctl start postgresql
sudo systemctl enable postgresql
log_success "PostgreSQL service started and enabled"

# Install Chrome (required for scraping)
log_info "Installing Google Chrome..."
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install -y google-chrome-stable
log_success "Google Chrome installed"

# Install ChromeDriver
log_info "Installing ChromeDriver..."
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d. -f1)
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}")
wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"
sudo unzip /tmp/chromedriver.zip -d /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
rm /tmp/chromedriver.zip
log_success "ChromeDriver installed"

# Install system dependencies for Python packages
log_info "Installing system dependencies..."
sudo apt install -y \
    build-essential \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    tk-dev \
    tcl-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libxcb1-dev
log_success "System dependencies installed"

# Create project directory
PROJECT_DIR="/home/$(whoami)/legal_management"
log_info "Creating project directory: $PROJECT_DIR"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Create Python virtual environment
log_info "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
log_success "Virtual environment created and activated"

# Install Python packages
log_info "Installing Python packages..."
pip install --upgrade pip

# Install core packages
pip install \
    flask==2.3.3 \
    flask-cors==4.0.0 \
    psycopg2-binary==2.9.7 \
    selenium==4.20.0 \
    pillow==10.0.1 \
    transformers==4.35.0 \
    torch==2.1.0 \
    torchvision==0.16.0 \
    requests==2.31.0 \
    python-dateutil==2.8.2

log_success "Python packages installed"

# Setup PostgreSQL database
log_info "Setting up PostgreSQL database..."

# Create database user
sudo -u postgres createuser -s prashanth 2>/dev/null || log_warning "User 'prashanth' already exists"

# Set password for user
sudo -u postgres psql -c "ALTER USER prashanth PASSWORD 'secure_password_123';" 2>/dev/null || log_warning "Password already set"

# Create database
sudo -u postgres createdb -O prashanth legal_management 2>/dev/null || log_warning "Database 'legal_management' already exists"

log_success "PostgreSQL database setup completed"

# Configure PostgreSQL for local connections
log_info "Configuring PostgreSQL..."
PG_VERSION=$(sudo -u postgres psql -t -c "SELECT version();" | grep -oP '\d+\.\d+' | head -1)
PG_CONFIG_DIR="/etc/postgresql/$PG_VERSION/main"

# Backup original files
sudo cp "$PG_CONFIG_DIR/postgresql.conf" "$PG_CONFIG_DIR/postgresql.conf.backup" 2>/dev/null || true
sudo cp "$PG_CONFIG_DIR/pg_hba.conf" "$PG_CONFIG_DIR/pg_hba.conf.backup" 2>/dev/null || true

# Configure postgresql.conf
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = 'localhost'/" "$PG_CONFIG_DIR/postgresql.conf"

# Configure pg_hba.conf for local connections
if ! sudo grep -q "local   all             prashanth                               md5" "$PG_CONFIG_DIR/pg_hba.conf"; then
    echo "local   all             prashanth                               md5" | sudo tee -a "$PG_CONFIG_DIR/pg_hba.conf"
fi

# Restart PostgreSQL
sudo systemctl restart postgresql
log_success "PostgreSQL configured and restarted"

# Create systemd service for the application
log_info "Creating systemd service..."
sudo tee /etc/systemd/system/legal-api.service > /dev/null <<EOF
[Unit]
Description=Legal Management API
After=network.target postgresql.service

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python legal_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
log_success "Systemd service created"

# Setup firewall
log_info "Configuring firewall..."
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 5002/tcp    # API server
sudo ufw allow 8000/tcp    # Web server
sudo ufw allow 5432/tcp    # PostgreSQL (local only)
sudo ufw --force enable
log_success "Firewall configured"

# Create startup script
log_info "Creating startup script..."
tee "$PROJECT_DIR/start_server.sh" > /dev/null <<EOF
#!/bin/bash
# Legal Management System Startup Script

cd "$PROJECT_DIR"
source venv/bin/activate

echo "🚀 Starting Legal Management System..."
echo "📍 Working directory: \$(pwd)"
echo "🐍 Python version: \$(python --version)"
echo "📦 Virtual environment: \$VIRTUAL_ENV"

# Run database migrations
echo "🗄️ Running database setup..."
python database_setup.py

# Start the API server
echo "🌐 Starting API server on port 5002..."
python legal_api.py
EOF

chmod +x "$PROJECT_DIR/start_server.sh"
log_success "Startup script created"

# Create deployment script
log_info "Creating deployment script..."
tee "$PROJECT_DIR/deploy.sh" > /dev/null <<EOF
#!/bin/bash
# Quick deployment script

echo "🔄 Deploying Legal Management System..."

# Stop service if running
sudo systemctl stop legal-api 2>/dev/null || true

# Copy files (assuming they're uploaded to ~/upload/)
if [ -d "~/upload/" ]; then
    echo "📁 Copying files from upload directory..."
    cp -r ~/upload/* .
    rm -rf ~/upload/
fi

# Run database migrations
echo "🗄️ Running database migrations..."
source venv/bin/activate
python migrate_database.py 2>/dev/null || python database_setup.py

# Start service
echo "🚀 Starting service..."
sudo systemctl start legal-api
sudo systemctl enable legal-api

echo "✅ Deployment completed!"
echo "🌐 API running on: http://\$(curl -s ifconfig.me):5002"
echo "📊 Check status: sudo systemctl status legal-api"
EOF

chmod +x "$PROJECT_DIR/deploy.sh"
log_success "Deployment script created"

# Create monitoring script
log_info "Creating monitoring script..."
tee "$PROJECT_DIR/monitor.sh" > /dev/null <<EOF
#!/bin/bash
# System monitoring script

echo "🔍 Legal Management System Status"
echo "=================================="

echo "📊 Service Status:"
sudo systemctl status legal-api --no-pager -l

echo ""
echo "🗄️ Database Status:"
sudo systemctl status postgresql --no-pager -l

echo ""
echo "🌐 Network Status:"
sudo netstat -tulpn | grep -E ':(5002|5432|8000)'

echo ""
echo "💾 Disk Usage:"
df -h

echo ""
echo "🧠 Memory Usage:"
free -h

echo ""
echo "📈 CPU Usage:"
top -bn1 | grep "Cpu(s)"

echo ""
echo "📝 Recent API Logs:"
journalctl -u legal-api --no-pager -n 10
EOF

chmod +x "$PROJECT_DIR/monitor.sh"
log_success "Monitoring script created"

# Create README
log_info "Creating README..."
tee "$PROJECT_DIR/README_EC2.md" > /dev/null <<EOF
# Legal Management System - EC2 Setup

## 🚀 Quick Start

### Start the system:
\`\`\`bash
./start_server.sh
\`\`\`

### Deploy new code:
1. Upload files to ~/upload/
2. Run: \`./deploy.sh\`

### Monitor system:
\`\`\`bash
./monitor.sh
\`\`\`

## 🔧 Manual Commands

### Database:
\`\`\`bash
# Connect to database
psql -U prashanth -d legal_management

# Run migrations
python database_setup.py
\`\`\`

### Service Management:
\`\`\`bash
# Start/stop service
sudo systemctl start legal-api
sudo systemctl stop legal-api
sudo systemctl restart legal-api

# Check status
sudo systemctl status legal-api

# View logs
journalctl -u legal-api -f
\`\`\`

### Testing:
\`\`\`bash
# Test API
curl http://localhost:5002/api/health

# Test database connection
python -c "from database_setup import DatabaseManager; db = DatabaseManager(); print('✅ DB OK' if db.get_connection() else '❌ DB Failed')"
\`\`\`

## 📁 Directory Structure:
- \`legal_api.py\` - Main API server
- \`database_setup.py\` - Database setup and migrations
- \`scrapper.py\` - Web scraping functionality
- \`*.html\` - Frontend files
- \`venv/\` - Python virtual environment
- \`start_server.sh\` - Start the system
- \`deploy.sh\` - Deploy new code
- \`monitor.sh\` - System monitoring

## 🌐 URLs:
- API: http://YOUR_EC2_IP:5002
- Web Interface: http://YOUR_EC2_IP:8000

## 🔐 Default Credentials:
- Database: prashanth / secure_password_123
- Admin User: admin / admin123
EOF

log_success "Documentation created"

# Final setup
log_info "Final setup steps..."
cd "$PROJECT_DIR"

echo ""
log_success "🎉 Installation completed successfully!"
echo ""
echo "📋 Next Steps:"
echo "1. Upload your project files to: $PROJECT_DIR"
echo "2. Run: ./start_server.sh"
echo "3. Access your API at: http://$(curl -s ifconfig.me 2>/dev/null || echo 'YOUR_EC2_IP'):5002"
echo ""
echo "📁 Project directory: $PROJECT_DIR"
echo "🔧 Useful commands:"
echo "   - Start server: ./start_server.sh"
echo "   - Deploy code: ./deploy.sh"
echo "   - Monitor system: ./monitor.sh"
echo "   - View logs: journalctl -u legal-api -f"
echo ""
log_warning "Remember to:"
echo "   - Configure your EC2 security groups to allow ports 5002 and 8000"
echo "   - Upload your project files to $PROJECT_DIR"
echo "   - Test the installation with ./start_server.sh"
echo ""
log_success "Installation complete! 🚀"
