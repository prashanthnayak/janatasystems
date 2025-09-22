#!/bin/bash
#
# Legal Case Management System - Complete Installation Script
# Amazon Linux 3 Compatible
#
# This script installs and configures the complete Legal Case Management System
# including all dependencies, services, and database setup.
#
# Usage: chmod +x install.sh && ./install.sh
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
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

log_step() {
    echo -e "${PURPLE}🔧 $1${NC}"
}

log_header() {
    echo -e "${CYAN}🚀 $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root. Please run as a regular user with sudo privileges."
        exit 1
    fi
}

# Check if sudo is available
check_sudo() {
    if ! sudo -n true 2>/dev/null; then
        log_error "This script requires sudo privileges. Please ensure your user can run sudo commands."
        exit 1
    fi
}

# Detect OS version
detect_os() {
    log_info "Detecting operating system..."
    
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VERSION=$VERSION_ID
    else
        log_error "Cannot detect operating system. This script is designed for Amazon Linux 3."
        exit 1
    fi
    
    log_success "Detected: $OS $VERSION"
    
    if [[ "$OS" != "Amazon Linux" ]] && [[ "$OS" != "Amazon Linux 2023" ]]; then
        log_warning "This script is optimized for Amazon Linux 3. Proceeding anyway..."
    fi
}

# Update system packages
update_system() {
    log_header "Updating system packages..."
    
    log_step "Updating package lists..."
    sudo dnf update -y
    
    log_step "Installing essential build tools..."
    sudo dnf groupinstall -y "Development Tools"
    
    log_step "Installing essential packages..."
    sudo dnf install -y \
        wget \
        curl \
        git \
        unzip \
        tar \
        gzip \
        which \
        procps \
        net-tools \
        htop \
        vim \
        nano \
        tree
    
    log_success "System packages updated successfully"
}

# Install Python 3.9+
install_python() {
    log_header "Installing Python 3.9+..."
    
    # Check if Python 3.9+ is already installed
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
        
        if [[ $PYTHON_MAJOR -eq 3 ]] && [[ $PYTHON_MINOR -ge 9 ]]; then
            log_success "Python $PYTHON_VERSION is already installed and meets requirements"
            return 0
        fi
    fi
    
    log_step "Installing Python 3.9+..."
    sudo dnf install -y python3 python3-pip python3-devel
    
    # Verify installation
    PYTHON_VERSION=$(python3 --version)
    log_success "Python installed: $PYTHON_VERSION"
    
    # Upgrade pip
    log_step "Upgrading pip..."
    python3 -m pip install --upgrade pip
    
    log_success "Python installation completed"
}

# Install PostgreSQL
install_postgresql() {
    log_header "Installing PostgreSQL..."
    
    # Check if PostgreSQL is already installed
    if command -v psql &> /dev/null; then
        log_success "PostgreSQL is already installed"
        return 0
    fi
    
    log_step "Installing PostgreSQL..."
    sudo dnf install -y postgresql15 postgresql15-server postgresql15-contrib
    
    log_step "Initializing PostgreSQL database..."
    sudo /usr/pgsql-15/bin/postgresql-15-setup initdb
    
    log_step "Enabling and starting PostgreSQL service..."
    sudo systemctl enable postgresql-15
    sudo systemctl start postgresql-15
    
    # Wait for PostgreSQL to start
    sleep 5
    
    log_step "Configuring PostgreSQL..."
    # Create database and user
    sudo -u postgres psql -c "CREATE DATABASE legal_cases;"
    sudo -u postgres psql -c "CREATE USER legal_user WITH PASSWORD 'legal_password_2024';"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE legal_cases TO legal_user;"
    sudo -u postgres psql -c "ALTER USER legal_user CREATEDB;"
    
    log_success "PostgreSQL installed and configured"
}

# Install Chrome and ChromeDriver
install_chrome() {
    log_header "Installing Google Chrome and ChromeDriver..."
    
    # Check if Chrome is already installed
    if command -v google-chrome &> /dev/null; then
        log_success "Google Chrome is already installed"
    else
        log_step "Installing Google Chrome..."
        
        # Handle curl conflicts
        if rpm -qa | grep -q curl-minimal; then
            log_info "curl-minimal detected, skipping curl installation"
        else
            sudo dnf install -y curl
        fi
        
        # Add Google Chrome repository
        sudo tee /etc/yum.repos.d/google-chrome.repo > /dev/null <<EOF
[google-chrome]
name=google-chrome
baseurl=http://dl.google.com/linux/chrome/rpm/stable/x86_64
enabled=1
gpgcheck=1
gpgkey=https://dl.google.com/linux/linux_signing_key.pub
EOF
        
        # Install Chrome
        sudo dnf install -y google-chrome-stable
        
        log_success "Google Chrome installed successfully"
    fi
    
    # Install ChromeDriver
    log_step "Installing ChromeDriver..."
    
    # Get Chrome version
    CHROME_VERSION=$(google-chrome --version | cut -d' ' -f3 | cut -d'.' -f1)
    log_info "Chrome version: $CHROME_VERSION"
    
    # Download ChromeDriver
    CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION")
    log_info "ChromeDriver version: $CHROMEDRIVER_VERSION"
    
    wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"
    unzip /tmp/chromedriver.zip -d /tmp/
    sudo mv /tmp/chromedriver /usr/local/bin/
    sudo chmod +x /usr/local/bin/chromedriver
    
    # Clean up
    rm /tmp/chromedriver.zip
    
    log_success "ChromeDriver installed successfully"
}

# Install Python dependencies
install_python_deps() {
    log_header "Installing Python dependencies..."
    
    log_step "Installing core Python packages..."
    pip3 install --user \
        flask \
        flask-cors \
        psycopg2-binary \
        sqlalchemy \
        requests \
        selenium \
        pillow \
        pytesseract \
        python-dotenv \
        gunicorn \
        bcrypt \
        cryptography
    
    log_success "Python dependencies installed"
}

# Setup database
setup_database() {
    log_header "Setting up database..."
    
    log_step "Creating database tables..."
    
    # Create a temporary Python script to setup database
    cat > /tmp/setup_db.py << 'EOF'
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'database': 'legal_cases',
    'user': 'legal_user',
    'password': 'legal_password_2024',
    'port': 5432
}

try:
    # Connect to PostgreSQL
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cases (
            id SERIAL PRIMARY KEY,
            cnr_number VARCHAR(50) UNIQUE NOT NULL,
            case_title TEXT NOT NULL,
            case_type VARCHAR(100),
            court_name VARCHAR(200),
            filing_date DATE,
            status VARCHAR(100),
            description TEXT,
            user_id INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS case_history (
            id SERIAL PRIMARY KEY,
            case_id INTEGER REFERENCES cases(id),
            hearing_date DATE,
            hearing_time TIME,
            purpose TEXT,
            status VARCHAR(100),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            email VARCHAR(100),
            phone VARCHAR(20),
            address TEXT,
            user_id INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cases_cnr ON cases(cnr_number)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cases_user ON cases(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_case_history_case ON case_history(case_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_clients_user ON clients(user_id)')
    
    # Insert default admin user
    cursor.execute('''
        INSERT INTO users (username, password_hash, role) 
        VALUES ('admin', 'admin_password_hash', 'admin')
        ON CONFLICT (username) DO NOTHING
    ''')
    
    print("Database setup completed successfully!")
    
except Exception as e:
    print(f"Database setup failed: {e}")
    exit(1)
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()
EOF
    
    # Run the database setup script
    python3 /tmp/setup_db.py
    rm /tmp/setup_db.py
    
    log_success "Database setup completed"
}

# Configure firewall
configure_firewall() {
    log_header "Configuring firewall..."
    
    log_step "Enabling firewall..."
    sudo systemctl enable firewalld
    sudo systemctl start firewalld
    
    log_step "Opening required ports..."
    sudo firewall-cmd --permanent --add-port=5000/tcp  # Flask API
    sudo firewall-cmd --permanent --add-port=8000/tcp  # Frontend
    sudo firewall-cmd --permanent --add-port=5432/tcp  # PostgreSQL
    sudo firewall-cmd --reload
    
    log_success "Firewall configured"
}

# Create systemd service
create_service() {
    log_header "Creating systemd service..."
    
    # Get current user and home directory
    CURRENT_USER=$(whoami)
    CURRENT_HOME=$(eval echo ~$CURRENT_USER)
    PROJECT_DIR=$(pwd)
    
    log_step "Creating legal-api service..."
    
    sudo tee /etc/systemd/system/legal-api.service > /dev/null <<EOF
[Unit]
Description=Legal Case Management API
After=network.target postgresql-15.service

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$CURRENT_HOME/.local/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/usr/bin/python3 $PROJECT_DIR/legal_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable legal-api.service
    
    log_success "Systemd service created and enabled"
}

# Start services
start_services() {
    log_header "Starting services..."
    
    log_step "Starting PostgreSQL..."
    sudo systemctl start postgresql-15
    
    log_step "Starting Legal API service..."
    sudo systemctl start legal-api.service
    
    # Wait for services to start
    sleep 5
    
    # Check service status
    if sudo systemctl is-active --quiet postgresql-15; then
        log_success "PostgreSQL is running"
    else
        log_error "PostgreSQL failed to start"
    fi
    
    if sudo systemctl is-active --quiet legal-api.service; then
        log_success "Legal API service is running"
    else
        log_warning "Legal API service may need manual start"
    fi
}

# Display final information
display_final_info() {
    log_header "Installation completed successfully!"
    
    echo ""
    echo -e "${GREEN}🎉 Legal Case Management System is now installed and running!${NC}"
    echo ""
    echo -e "${BLUE}📋 System Information:${NC}"
    echo -e "   • PostgreSQL: Running on port 5432"
    echo -e "   • Legal API: Running on port 5000"
    echo -e "   • Frontend: Available on port 8000"
    echo ""
    echo -e "${BLUE}🔑 Default Credentials:${NC}"
    echo -e "   • Username: admin"
    echo -e "   • Password: admin_password_hash"
    echo ""
    echo -e "${BLUE}🌐 Access URLs:${NC}"
    echo -e "   • API: http://$(curl -s ifconfig.me):5000"
    echo -e "   • Frontend: http://$(curl -s ifconfig.me):8000"
    echo ""
    echo -e "${BLUE}🔧 Service Management:${NC}"
    echo -e "   • Start API: sudo systemctl start legal-api"
    echo -e "   • Stop API: sudo systemctl stop legal-api"
    echo -e "   • Restart API: sudo systemctl restart legal-api"
    echo -e "   • Check status: sudo systemctl status legal-api"
    echo ""
    echo -e "${BLUE}📚 Next Steps:${NC}"
    echo -e "   1. Update the admin password in the database"
    echo -e "   2. Configure your domain/IP in config.js"
    echo -e "   3. Test the system by accessing the frontend"
    echo -e "   4. Add your first case and client"
    echo ""
    echo -e "${GREEN}✨ Installation completed successfully!${NC}"
}

# Main installation function
main() {
    log_header "Legal Case Management System - Complete Installation"
    echo "=========================================================="
    echo ""
    
    # Pre-installation checks
    check_root
    check_sudo
    detect_os
    
    # Installation steps
    update_system
    install_python
    install_postgresql
    install_chrome
    install_python_deps
    setup_database
    configure_firewall
    create_service
    start_services
    
    # Final information
    display_final_info
}

# Run main function
main "$@"
