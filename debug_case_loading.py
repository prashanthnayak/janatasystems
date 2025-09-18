#!/usr/bin/env python3
"""
Debug case loading - check database, API, and frontend flow
"""

import requests
import json
from database_setup import DatabaseManager

def check_database_cases():
    """Check what's actually in the database"""
    print("🗄️ CHECKING DATABASE")
    print("=" * 50)
    
    try:
        db = DatabaseManager()
        cases = db.get_all_cases()
        
        if not cases:
            print("❌ No cases found in database")
            return False
        
        print(f"✅ Found {len(cases)} case(s) in database:")
        for i, case in enumerate(cases, 1):
            print(f"\n📋 Case {i}:")
            print(f"   CNR: {case.get('cnr_number', 'N/A')}")
            print(f"   Title: {case.get('case_title', 'N/A')}")
            print(f"   Client: {case.get('client_name', 'N/A')}")
            print(f"   Petitioner: {case.get('petitioner', 'N/A')}")
            print(f"   Type: {case.get('case_type', 'N/A')}")
            print(f"   Status: {case.get('status', 'N/A')}")
            print(f"   User ID: {case.get('user_id', 'N/A')}")
            print(f"   Created: {case.get('created_at', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def check_api_cases():
    """Check if API returns cases"""
    print("\n🌐 CHECKING API ENDPOINTS")
    print("=" * 50)
    
    base_url = "http://localhost:5002/api"
    
    # First login to get token
    print("1. Testing login...")
    try:
        login_data = {"username": "admin", "password": "admin123"}
        response = requests.post(f"{base_url}/auth/login", json=login_data)
        
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
        login_result = response.json()
        if not login_result.get('success'):
            print(f"❌ Login unsuccessful: {login_result.get('error')}")
            return False
            
        token = login_result.get('token')
        print(f"✅ Login successful, got token: {token[:20]}...")
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Test cases API
    print("\n2. Testing cases API...")
    try:
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(f"{base_url}/cases", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Cases API failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
        result = response.json()
        print(f"   Response: {json.dumps(result, indent=2)}")
        
        if result.get('success'):
            cases = result.get('cases', [])
            print(f"✅ API returned {len(cases)} case(s)")
            
            for i, case in enumerate(cases, 1):
                print(f"\n📋 API Case {i}:")
                print(f"   CNR: {case.get('cnr_number', 'N/A')}")
                print(f"   Title: {case.get('case_title', 'N/A')}")
                print(f"   Client: {case.get('client_name', 'N/A')}")
                print(f"   User ID: {case.get('user_id', 'N/A')}")
            
            return len(cases) > 0
        else:
            print(f"❌ API returned error: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Cases API error: {e}")
        return False

def check_user_permissions():
    """Check user permissions and sessions"""
    print("\n🔐 CHECKING USER PERMISSIONS")
    print("=" * 50)
    
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check users
        cursor.execute("SELECT id, username, role FROM users")
        users = cursor.fetchall()
        print(f"📋 Users in database:")
        for user in users:
            print(f"   ID: {user[0]}, Username: {user[1]}, Role: {user[2]}")
        
        # Check active sessions
        cursor.execute("""
            SELECT us.user_id, u.username, us.session_token, us.expires_at > NOW() as active
            FROM user_sessions us
            JOIN users u ON us.user_id = u.id
            ORDER BY us.created_at DESC
            LIMIT 5
        """)
        sessions = cursor.fetchall()
        print(f"\n📋 Recent sessions:")
        for session in sessions:
            status = "✅ Active" if session[3] else "❌ Expired"
            print(f"   User ID: {session[0]} ({session[1]}) - {status}")
        
        # Check cases with user info
        cursor.execute("""
            SELECT c.cnr_number, c.case_title, c.user_id, u.username
            FROM cases c
            LEFT JOIN users u ON c.user_id = u.id
        """)
        cases_with_users = cursor.fetchall()
        print(f"\n📋 Cases with user mapping:")
        for case in cases_with_users:
            print(f"   CNR: {case[0]}, User ID: {case[2]}, Username: {case[3] or 'N/A'}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ User permissions check error: {e}")
        return False

def check_api_server_running():
    """Check if API server is running"""
    print("\n🚀 CHECKING API SERVER")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:5002/api/server-info", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ API server is running")
            print(f"   Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ API server responded with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API server not accessible: {e}")
        return False

def main():
    """Run all checks"""
    print("🔍 COMPREHENSIVE CASE LOADING DEBUG")
    print("=" * 60)
    
    # Check each component
    checks = [
        ("API Server", check_api_server_running),
        ("Database Cases", check_database_cases),
        ("User Permissions", check_user_permissions),
        ("API Cases", check_api_cases),
    ]
    
    results = {}
    for check_name, check_func in checks:
        print(f"\n{'='*60}")
        results[check_name] = check_func()
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 SUMMARY")
    print("=" * 60)
    
    for check_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name}: {status}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if not results.get("API Server"):
        print("   🔧 Start API server: python3 legal_api.py")
    
    if not results.get("Database Cases"):
        print("   🔧 No cases in database - add some cases first")
    
    if results.get("Database Cases") and not results.get("API Cases"):
        print("   🔧 Database has cases but API doesn't return them")
        print("      - Check user permissions")
        print("      - Check if cases belong to the logged-in user")
        print("      - Check API filtering logic")
    
    if results.get("API Cases"):
        print("   🔧 API works - check frontend JavaScript console")
        print("      - Open browser F12 console")
        print("      - Look for API call errors")
        print("      - Check if frontend is calling correct URLs")

if __name__ == "__main__":
    main()
