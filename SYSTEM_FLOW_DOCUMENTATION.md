# Legal Case Management System - Flow Documentation

## 📋 Table of Contents
1. [System Architecture Overview](#system-architecture-overview)
2. [Authentication Flow](#authentication-flow)
3. [Case Management Flow](#case-management-flow)
4. [Scraping Flow](#scraping-flow)
5. [Dashboard & Caching Flow](#dashboard--caching-flow)
6. [Admin Dashboard Flow](#admin-dashboard-flow)
7. [API Endpoints Reference](#api-endpoints-reference)
8. [Database Schema](#database-schema)
9. [Frontend-Backend Communication](#frontend-backend-communication)

---

## 🏗️ System Architecture Overview

### **Components**
- **Frontend**: HTML/CSS/JavaScript (Port 8000)
- **Backend API**: Flask/Python (Port 5002)
- **Database**: PostgreSQL (Port 5432)
- **Scraping Engine**: Selenium + Chrome + TrOCR
- **Web Server**: Python HTTP Server

### **Key Files**
```
├── Frontend Pages
│   ├── login.html              # User authentication
│   ├── legal_dashboard.html    # Main dashboard
│   ├── cases.html             # Case management
│   ├── add_case.html          # Add new cases
│   ├── edit_case.html         # Edit existing cases
│   ├── case_details.html      # Case details & timeline
│   ├── clients.html           # Client management
│   ├── calendar.html          # Calendar view
│   └── admin_dashboard.html   # Admin panel
│
├── Backend
│   ├── legal_api.py           # Main Flask API
│   ├── database_setup.py      # Database operations
│   └── scrapper.py            # eCourts scraping
│
├── Configuration
│   ├── config.js              # Dynamic URL configuration
│   └── requirements.txt       # Python dependencies
│
└── Installation Scripts
    ├── install_ec2_amazon_linux.sh
    ├── install_chrome_amazon_linux.sh
    └── fix_chromedriver_new.sh
```

---

## 🔐 Authentication Flow

### **1. Login Process**
```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend (login.html)
    participant A as API (legal_api.py)
    participant D as Database (PostgreSQL)
    
    U->>F: Enter username/password
    F->>A: POST /api/auth/login
    A->>D: authenticate_user(username, password)
    D-->>A: User data (if valid)
    A->>D: create_user_session(user_id, token, expires_at)
    A-->>F: {success: true, token, user_data}
    F->>F: Store token in localStorage
    F->>F: Redirect to legal_dashboard.html
```

### **2. Session Management**
- **Token Generation**: `secrets.token_urlsafe(32)` (32-character URL-safe token)
- **Session Duration**: 24 hours
- **Storage**: `user_sessions` table with `user_id`, `session_token`, `expires_at`
- **Validation**: `@require_auth` decorator checks token on protected endpoints

### **3. Logout Process**
```mermaid
sequenceDiagram
    participant F as Frontend
    participant A as API
    participant D as Database
    
    F->>A: POST /api/auth/logout (with Bearer token)
    A->>D: DELETE FROM user_sessions WHERE session_token = ?
    A-->>F: {success: true}
    F->>F: Clear localStorage
    F->>F: Redirect to login.html
```

---

## 📁 Case Management Flow

### **1. Add New Case Flow**
```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend (add_case.html)
    participant A as API (legal_api.py)
    participant S as Scraper (scrapper.py)
    participant E as eCourts Website
    participant D as Database
    
    U->>F: Enter CNR number
    F->>A: POST /api/scraping/trigger/{cnrNumber}
    A->>S: scrape_case_details(cnrNumber)
    S->>E: Navigate to eCourts website
    E-->>S: Case details page
    S->>S: Solve CAPTCHA with TrOCR
    S->>E: Submit form with CNR + CAPTCHA
    E-->>S: Case history table
    S-->>A: Scraped case data
    A-->>F: {success: true, case_data}
    F->>F: Pre-fill form with scraped data
    U->>F: Review and submit form
    F->>A: POST /api/cases/save
    A->>D: INSERT INTO cases + case_history
    A-->>F: {success: true}
    F->>F: Clear cache, redirect to cases.html
```

### **2. Case Display Flow**
```mermaid
sequenceDiagram
    participant F as Frontend (cases.html)
    participant A as API (legal_api.py)
    participant D as Database
    participant C as Cache (localStorage)
    
    F->>C: Check localStorage for cached data
    alt Cache Hit
        C-->>F: Return cached cases
        F->>F: Display cases instantly
    else Cache Miss
        F->>A: GET /api/cases?limit=50&offset=0
        A->>D: SELECT * FROM cases WHERE user_id = ?
        D-->>A: Cases data
        A-->>F: {success: true, cases: [...]}
        F->>C: Store in localStorage
        F->>F: Display cases
    end
```

### **3. Case Details Flow**
```mermaid
sequenceDiagram
    participant F as Frontend (case_details.html)
    participant A as API (legal_api.py)
    participant D as Database
    
    F->>A: GET /api/cases/{cnrNumber}
    A->>D: SELECT * FROM cases WHERE cnr_number = ?
    D-->>A: Case data
    A-->>F: {success: true, case: {...}}
    
    F->>A: GET /api/case_history/{cnrNumber}
    A->>D: SELECT * FROM case_history WHERE cnr_number = ?
    D-->>A: History data
    A-->>F: {success: true, history: [...]}
    
    F->>F: Display case details + timeline
```

---

## 🕷️ Scraping Flow

### **1. eCourts Scraping Process**
```mermaid
sequenceDiagram
    participant A as API
    participant S as Scraper
    participant C as Chrome Driver
    participant E as eCourts Website
    participant O as TrOCR Model
    
    A->>S: scrape_case_details(cnrNumber)
    S->>C: Create Chrome driver (headless)
    C->>E: Navigate to https://services.ecourts.gov.in/ecourtindia_v6/
    E-->>C: Homepage with CAPTCHA
    C->>S: Screenshot CAPTCHA image
    S->>O: Process CAPTCHA with TrOCR
    O-->>S: Solved CAPTCHA text
    S->>C: Enter CNR + CAPTCHA
    C->>E: Submit form
    E-->>C: Case details page
    C->>S: Extract case data + history table
    S->>C: Close driver
    S-->>A: {success: true, case_data: {...}}
```

### **2. Scraping Configuration**
- **Headless Mode**: `HEADLESS = True` for EC2
- **Chrome Options**: `--no-sandbox`, `--disable-dev-shm-usage`, `--disable-gpu`
- **CAPTCHA Solving**: TrOCR model `anuashok/ocr-captcha-v3`
- **Retry Logic**: 3 attempts with exponential backoff
- **Data Extraction**: Case details + hearing history table

---

## 📊 Dashboard & Caching Flow

### **1. Dashboard Data Loading**
```mermaid
sequenceDiagram
    participant F as Frontend (legal_dashboard.html)
    participant A as API (legal_api.py)
    participant D as Database
    participant C as Cache (localStorage)
    
    F->>C: Check window.userDashboardData
    alt Memory Cache Hit
        C-->>F: Return cached data
        F->>F: Display dashboard instantly
    else Memory Cache Miss
        F->>C: Check localStorage.userDashboardData
        alt Storage Cache Hit
            C-->>F: Return cached data
            F->>F: Display dashboard
        else Storage Cache Miss
            F->>A: GET /api/user/dashboard-data
            A->>D: Get cases + case_histories + user_stats
            D-->>A: Dashboard data
            A-->>F: {success: true, dashboard_data: {...}}
            F->>C: Store in localStorage + window
            F->>F: Display dashboard
        end
    end
```

### **2. Cache Invalidation**
```mermaid
sequenceDiagram
    participant P1 as Page 1 (add_case.html)
    participant P2 as Page 2 (cases.html)
    participant C as Cache (localStorage)
    
    P1->>P1: Save case successfully
    P1->>C: localStorage.removeItem('userDashboardData')
    P1->>C: localStorage.setItem('cacheUpdated', timestamp)
    
    P2->>C: Check localStorage.getItem('cacheUpdated')
    C-->>P2: New timestamp detected
    P2->>P2: Reload data from API
    P2->>C: Update cache
```

### **3. Real-time Updates**
- **Cache Clearing**: After add/edit/delete operations
- **Cross-page Sync**: `localStorage.setItem('cacheUpdated', timestamp)`
- **Auto-refresh**: Pages check for cache updates every 1 second
- **Performance**: Instant display from cache, background API refresh

---

## 👨‍💼 Admin Dashboard Flow

### **1. User Management**
```mermaid
sequenceDiagram
    participant A as Admin
    participant F as Frontend (admin_dashboard.html)
    participant API as API (legal_api.py)
    participant D as Database
    
    A->>F: Click "Add User"
    F->>F: Show add user modal
    A->>F: Fill user details
    F->>API: POST /api/admin/users
    API->>D: INSERT INTO users
    D-->>API: User created
    API-->>F: {success: true}
    F->>F: Refresh user list
    F->>F: Show success notification
```

### **2. System Monitoring**
```mermaid
sequenceDiagram
    participant F as Frontend (admin_dashboard.html)
    participant API as API (legal_api.py)
    participant D as Database
    participant S as Scraper
    
    F->>API: GET /api/server-info
    API-->>F: Server status + IP info
    
    F->>API: GET /api/health/database
    API->>D: Test connection
    D-->>API: Connection status
    API-->>F: Database health
    
    F->>API: GET /api/health/scraping
    API->>S: Test Chrome + ChromeDriver
    S-->>API: Scraping engine status
    API-->>F: Scraping health
```

---

## 🔌 API Endpoints Reference

### **Authentication Endpoints**
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/login` | User login | No |
| POST | `/api/auth/logout` | User logout | Yes |
| GET | `/api/server-info` | Server information | No |

### **Case Management Endpoints**
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/cases` | Get all cases | Yes |
| GET | `/api/cases/{cnr}` | Get specific case | Yes |
| POST | `/api/cases/save` | Save new case | Yes |
| PUT | `/api/cases/{cnr}` | Update case | Yes |
| DELETE | `/api/cases/{cnr}` | Delete case | Yes |
| GET | `/api/case_history/{cnr}` | Get case history | Yes |

### **Scraping Endpoints**
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/scraping/trigger/{cnr}` | Trigger scraping | Yes |
| GET | `/api/health/scraping` | Check scraping health | Yes |

### **Dashboard Endpoints**
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/user/dashboard-data` | Get dashboard data | Yes |
| GET | `/api/user/profile` | Get user profile | Yes |

### **Admin Endpoints**
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/admin/users` | Get all users | Yes (Admin) |
| POST | `/api/admin/users` | Create user | Yes (Admin) |
| PUT | `/api/admin/users/{id}` | Update user | Yes (Admin) |
| DELETE | `/api/admin/users/{id}` | Delete user | Yes (Admin) |
| GET | `/api/health/database` | Database health | Yes (Admin) |

---

## 🗄️ Database Schema

### **Users Table**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    phone VARCHAR(15),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **User Sessions Table**
```sql
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **Cases Table**
```sql
CREATE TABLE cases (
    id SERIAL PRIMARY KEY,
    cnr_number VARCHAR(50) UNIQUE NOT NULL,
    case_title VARCHAR(255),
    petitioner VARCHAR(255),
    respondent VARCHAR(255),
    case_type VARCHAR(100),
    filing_date DATE,
    court_name VARCHAR(255),
    judge_name VARCHAR(255),
    registration_number VARCHAR(100),
    status VARCHAR(50),
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **Case History Table**
```sql
CREATE TABLE case_history (
    id SERIAL PRIMARY KEY,
    cnr_number VARCHAR(50) REFERENCES cases(cnr_number),
    hearing_date DATE,
    purpose_of_hearing TEXT,
    status VARCHAR(50),
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🌐 Frontend-Backend Communication

### **1. Dynamic URL Configuration**
```javascript
// config.js - Dynamic IP detection
class Config {
    async init() {
        try {
            const response = await fetch(`http://${window.location.hostname}:5002/api/server-info`);
            const data = await response.json();
            this.API_HOST = data.public_ip || window.location.hostname;
        } catch (error) {
            this.API_HOST = window.location.hostname;
        }
    }
    
    getApiUrl(endpoint = '') {
        return `http://${this.API_HOST}:5002/api${endpoint}`;
    }
}
```

### **2. Authentication Headers**
```javascript
// All API calls include authentication
const response = await fetch(url, {
    headers: {
        'Authorization': `Bearer ${localStorage.getItem('userToken')}`,
        'Content-Type': 'application/json'
    }
});
```

### **3. Error Handling**
```javascript
// 401 Unauthorized handling
if (response.status === 401) {
    localStorage.removeItem('userToken');
    localStorage.removeItem('userRole');
    window.location.href = 'login.html';
    return;
}
```

### **4. CORS Configuration**
```python
# legal_api.py - Dynamic CORS origins
def get_cors_origins():
    try:
        response = requests.get(f"http://{socket.gethostbyname(socket.gethostname())}:5002/api/server-info")
        data = response.json()
        return [
            f"http://{data['public_ip']}:8000",
            f"http://{data['public_ip']}:5002",
            "http://localhost:8000",
            "http://127.0.0.1:8000"
        ]
    except:
        return ["http://localhost:8000", "http://127.0.0.1:8000"]
```

---

## 🚀 Performance Optimizations

### **1. Caching Strategy**
- **Memory Cache**: `window.userDashboardData` for instant access
- **Storage Cache**: `localStorage.userDashboardData` for persistence
- **API Cache**: Pre-built calendar events from backend
- **Cache Invalidation**: Timestamp-based cross-page sync

### **2. Lazy Loading**
- **Pagination**: Cases loaded in batches of 50
- **Progressive Enhancement**: Cache-first, API fallback
- **Background Refresh**: Non-blocking cache updates

### **3. Network Optimization**
- **Batch Requests**: Multiple case histories in single API call
- **Compression**: Gzip compression for API responses
- **Connection Pooling**: Database connection reuse

---

## 🔧 Deployment Flow

### **1. EC2 Setup**
```bash
# Install dependencies
./install_ec2_amazon_linux.sh

# Install Chrome & ChromeDriver
./install_chrome_amazon_linux.sh

# Start services
sudo systemctl start postgresql
python3 legal_api.py &
python3 -m http.server 8000 &
```

### **2. Service Management**
- **PostgreSQL**: `systemctl start/stop postgresql`
- **API Server**: `python3 legal_api.py` (Port 5002)
- **Web Server**: `python3 -m http.server 8000` (Port 8000)
- **Firewall**: Ports 5002, 8000, 5432 open

---

## 📝 Key Features

### **✅ Implemented Features**
- User authentication with session management
- Case management (CRUD operations)
- eCourts scraping with CAPTCHA solving
- Real-time dashboard with caching
- Admin panel with user management
- Calendar view with hearing dates
- Client management
- Case details with timeline
- Cross-page cache synchronization
- Dynamic IP configuration
- Responsive design with Grammarly theme

### **🔧 Technical Features**
- Headless Chrome scraping
- TrOCR CAPTCHA solving
- PostgreSQL database
- Flask REST API
- JavaScript ES6+
- CSS Grid/Flexbox
- Local storage caching
- CORS handling
- Error handling & logging
- Amazon Linux 3 compatibility

---

## 🎯 System Flow Summary

1. **User logs in** → Token stored → Redirect to dashboard
2. **Dashboard loads** → Check cache → Display data instantly
3. **Add case** → Scrape eCourts → Save to database → Clear cache
4. **View cases** → Load from cache → Display with pagination
5. **Case details** → Load case + history → Display timeline
6. **Calendar view** → Process hearing dates → Display events
7. **Admin panel** → Manage users → Monitor system health
8. **Logout** → Clear session → Redirect to login

**The system provides a complete legal case management solution with real-time data synchronization, automated scraping, and professional user interface.**
