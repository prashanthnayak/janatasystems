# Legal Case Management System - Complete Documentation

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Installation Guide](#installation-guide)
3. [System Architecture](#system-architecture)
4. [API Reference](#api-reference)
5. [Database Schema](#database-schema)
6. [Frontend Architecture](#frontend-architecture)
7. [Authentication & Security](#authentication--security)
8. [Scraping System](#scraping-system)
9. [Deployment Guide](#deployment-guide)
10. [Troubleshooting](#troubleshooting)
11. [User Management](#user-management)
12. [Development Guidelines](#development-guidelines)

---

## 🎯 System Overview

The Legal Case Management System is a comprehensive web application designed for legal practices to manage cases, clients, and court hearings efficiently.

### Key Features
- ✅ **Case Management** - Add, edit, view, and delete legal cases
- ✅ **Client Management** - Manage client information and relationships
- ✅ **Calendar Integration** - Track hearings and important dates
- ✅ **eCourts Integration** - Automatic case data scraping from court websites
- ✅ **Multi-user Support** - Role-based access control (Admin/User)
- ✅ **Real-time Updates** - Live data synchronization across pages
- ✅ **Admin Dashboard** - System monitoring and user management

### Technology Stack
- **Backend**: Flask (Python 3.9+)
- **Database**: PostgreSQL 15
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Scraping**: Selenium + Chrome/ChromeDriver
- **Deployment**: Amazon Linux 3, systemd services

---

## 🚀 Installation Guide

### Prerequisites
- Amazon Linux 3 EC2 instance
- User with sudo privileges
- Internet connection
- Minimum 2GB RAM, 20GB storage

### One-Command Installation

```bash
# Download and run the installation script
curl -sSL https://raw.githubusercontent.com/your-repo/legal-case-management/main/install.sh | bash
```

Or manually:

```bash
# Clone the repository
git clone https://github.com/your-repo/legal-case-management.git
cd legal-case-management

# Make install script executable
chmod +x install.sh

# Run installation
./install.sh
```

### What Gets Installed
- ✅ **System Updates** - Latest packages and security updates
- ✅ **Python 3.9+** - With pip and development tools
- ✅ **PostgreSQL 15** - Database server with legal_cases database
- ✅ **Google Chrome** - Latest stable version
- ✅ **ChromeDriver** - Matching version for web scraping
- ✅ **Python Dependencies** - Flask, Selenium, psycopg2, etc.
- ✅ **Database Setup** - Tables, indexes, and default admin user
- ✅ **Firewall Configuration** - Ports 5000, 8000, 5432
- ✅ **Systemd Service** - Auto-start on boot
- ✅ **Service Startup** - All services running

### Default Credentials
- **Username:** `admin`
- **Password:** `admin_password_hash`

**⚠️ Important:** Change the default password after installation!

### Access URLs
- **Frontend:** `http://your-server-ip:8000`
- **API:** `http://your-server-ip:5000`

---

## 🏗️ System Architecture

### Backend Architecture
```
legal_api.py (Flask Application)
├── Authentication Layer
├── API Endpoints
├── Database Layer (PostgreSQL)
├── Scraping Engine (Selenium)
└── Service Management (systemd)
```

### Frontend Architecture
```
HTML Pages
├── login.html (Authentication)
├── legal_dashboard.html (Main Dashboard)
├── cases.html (Case Management)
├── add_case.html (Add Cases)
├── edit_case.html (Edit Cases)
├── case_details.html (View Cases)
├── clients.html (Client Management)
├── calendar.html (Calendar View)
└── admin_dashboard.html (Admin Panel)

Shared Resources
├── config.js (Configuration)
├── common.js (Utilities)
└── shared-dashboard-styles.css (Styles)
```

### Data Flow
1. **User Authentication** → JWT-like token storage
2. **API Calls** → Flask backend with PostgreSQL
3. **Real-time Updates** → localStorage caching + cache invalidation
4. **Scraping** → Selenium + Chrome/ChromeDriver → Database
5. **Service Management** → systemd for auto-start

---

## 🔌 API Reference

### Authentication Endpoints
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/verify` - Verify token

### Case Management Endpoints
- `GET /api/cases` - Get all cases
- `POST /api/cases` - Create new case
- `GET /api/cases/{cnr}` - Get specific case
- `PUT /api/cases/{cnr}` - Update case
- `DELETE /api/cases/{cnr}` - Delete case

### Client Management Endpoints
- `GET /api/clients` - Get all clients
- `POST /api/clients` - Create new client
- `GET /api/clients/{id}` - Get specific client
- `PUT /api/clients/{id}` - Update client
- `DELETE /api/clients/{id}` - Delete client

### Dashboard Endpoints
- `GET /api/user/dashboard-data` - Get dashboard data
- `GET /api/user/case-history/{cnr}` - Get case history

### Scraping Endpoints
- `POST /api/scrape/case` - Trigger case scraping
- `GET /api/scrape/status` - Get scraping status

### Admin Endpoints
- `GET /api/admin/users` - Get all users
- `POST /api/admin/users` - Create user
- `PUT /api/admin/users/{id}` - Update user
- `DELETE /api/admin/users/{id}` - Delete user

---

## 🗄️ Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Cases Table
```sql
CREATE TABLE cases (
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
);
```

### Case History Table
```sql
CREATE TABLE case_history (
    id SERIAL PRIMARY KEY,
    case_id INTEGER REFERENCES cases(id),
    hearing_date DATE,
    hearing_time TIME,
    purpose TEXT,
    status VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Clients Table
```sql
CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🎨 Frontend Architecture

### Configuration System
- **`config.js`** - Dynamic configuration management
- **Dynamic IP handling** - No hardcoded IPs
- **Environment detection** - Development vs production

### Common Utilities
- **`common.js`** - Centralized utility functions
- **Logger system** - Categorized logging (debug, info, success, warning, error)
- **Alert system** - Custom styled modals instead of browser alerts
- **API utilities** - Centralized API call patterns
- **Cache management** - localStorage utilities
- **Form validation** - Centralized validation patterns

### Styling System
- **`shared-dashboard-styles.css`** - Centralized CSS system
- **Component-based CSS** - Reusable button, form, card components
- **CSS variables** - Consistent color palette and spacing
- **Responsive design** - Mobile-first approach
- **Professional theme** - Clean, modern interface

### Page Structure
- **Authentication** - `login.html`
- **Main Dashboard** - `legal_dashboard.html`
- **Case Management** - `cases.html`, `add_case.html`, `edit_case.html`, `case_details.html`
- **Client Management** - `clients.html`, `edit_client.html`, `client_details.html`
- **Calendar** - `calendar.html`
- **Admin Panel** - `admin_dashboard.html`

---

## 🔐 Authentication & Security

### Authentication Flow
1. **Login** → Username/password validation
2. **Token Generation** → JWT-like token stored in localStorage
3. **API Calls** → Token included in Authorization header
4. **Token Verification** → Backend validates token on each request
5. **Logout** → Token cleared from localStorage

### Security Features
- **Password Hashing** - SHA-256 with salt
- **Token-based Authentication** - Secure API access
- **Role-based Access Control** - Admin vs User roles
- **Input Validation** - Frontend and backend validation
- **SQL Injection Prevention** - Parameterized queries
- **CORS Configuration** - Proper cross-origin handling

### User Roles
- **Admin** - Full system access, user management
- **User** - Case and client management only

---

## 🕷️ Scraping System

### eCourts Integration
- **Automatic Case Data Fetching** - CNR number lookup
- **CAPTCHA Solving** - TrOCR-based CAPTCHA handling
- **Real-time Updates** - Fresh data from court websites
- **Error Handling** - Robust error recovery

### Scraping Flow
1. **User Input** → CNR number entered
2. **Chrome Launch** → Headless browser initialization
3. **Website Navigation** → eCourts website access
4. **CAPTCHA Handling** → Automatic CAPTCHA solving
5. **Data Extraction** → Case details extraction
6. **Database Storage** → Data saved to PostgreSQL
7. **Frontend Update** → Real-time UI updates

### Technical Details
- **Selenium WebDriver** - Browser automation
- **Chrome/ChromeDriver** - Latest stable versions
- **TrOCR** - CAPTCHA text recognition
- **Error Recovery** - Automatic retry mechanisms

---

## 🚀 Deployment Guide

### EC2 Setup
1. **Launch Amazon Linux 3 Instance**
2. **Configure Security Groups** - Ports 22, 5000, 8000, 5432
3. **Run Installation Script** - `./install.sh`
4. **Verify Services** - Check all services are running

### Service Management
```bash
# Check service status
sudo systemctl status legal-api

# Start service
sudo systemctl start legal-api

# Stop service
sudo systemctl stop legal-api

# Restart service
sudo systemctl restart legal-api

# View logs
sudo journalctl -u legal-api -f
```

### Production Considerations
- **SSL Certificates** - Set up HTTPS
- **Domain Configuration** - Configure domain name
- **Backup Strategy** - Regular database backups
- **Monitoring** - System health monitoring
- **Log Management** - Centralized logging

---

## 🛠️ Troubleshooting

### Common Issues

#### Chrome/ChromeDriver Issues
- **Version Mismatch** - Install script handles version matching
- **Permission Issues** - Ensure ChromeDriver is executable
- **Headless Mode** - Check Chrome headless configuration

#### Database Issues
- **Connection Errors** - Verify PostgreSQL is running
- **Permission Issues** - Check database user permissions
- **Table Missing** - Run database setup script

#### API Issues
- **CORS Errors** - Check CORS configuration
- **Authentication Errors** - Verify token validity
- **Port Conflicts** - Ensure ports 5000, 8000 are available

#### Frontend Issues
- **Cache Issues** - Clear browser cache
- **JavaScript Errors** - Check browser console
- **Styling Issues** - Verify CSS file loading

### Debugging Steps
1. **Check Service Status** - `sudo systemctl status legal-api`
2. **View Logs** - `sudo journalctl -u legal-api -f`
3. **Test API** - `curl http://localhost:5000/api/health`
4. **Check Database** - `sudo -u postgres psql legal_cases`
5. **Browser Console** - Check for JavaScript errors

---

## 👥 User Management

### Default Users
- **Admin User** - `admin` / `admin_password_hash`
- **Test User** - `shantharam` / `shantharam_password`

### Creating New Users
1. **Admin Login** - Access admin dashboard
2. **User Management** - Navigate to user management section
3. **Add User** - Fill in username and password
4. **Assign Role** - Set user or admin role
5. **Save** - User created and ready to use

### User Permissions
- **Admin Users** - Full system access, user management
- **Regular Users** - Case and client management only

---

## 💻 Development Guidelines

### Code Organization
- **Centralized Utilities** - Use `common.js` for shared functions
- **Consistent Styling** - Use `shared-dashboard-styles.css`
- **Dynamic Configuration** - Use `config.js` for all settings
- **Error Handling** - Implement proper error handling
- **Logging** - Use centralized logging system

### Best Practices
- **No Hardcoded Values** - Use configuration files
- **Input Validation** - Validate all user inputs
- **Error Recovery** - Implement graceful error handling
- **Performance** - Optimize API calls and caching
- **Security** - Follow security best practices

### File Structure
```
project/
├── install.sh (Installation script)
├── legal_api.py (Main Flask application)
├── database_setup.py (Database management)
├── scrapper.py (Web scraping)
├── config.js (Configuration)
├── common.js (Utilities)
├── shared-dashboard-styles.css (Styles)
├── *.html (Frontend pages)
└── requirements.txt (Python dependencies)
```

---

## 📞 Support

### Getting Help
1. **Check Documentation** - Review this guide
2. **Check Logs** - Review system logs
3. **Test Components** - Test individual components
4. **Community Support** - GitHub issues

### System Requirements
- **OS**: Amazon Linux 3
- **Python**: 3.9+
- **PostgreSQL**: 15+
- **Chrome**: Latest stable
- **RAM**: Minimum 2GB
- **Storage**: Minimum 20GB

---

**🎉 That's it! Your Legal Case Management System is ready to use!**

For additional support or questions, please refer to the troubleshooting section or create an issue in the project repository.
