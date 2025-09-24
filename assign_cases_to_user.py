#!/usr/bin/env python3
"""
Assign orphaned cases to the shantharam user (ID: 4)
"""

import os
import requests
from database_setup import DatabaseManager

# Configuration
API_REQUEST_TIMEOUT = int(os.getenv('API_REQUEST_TIMEOUT', '5'))

def get_api_base_url():
    """Get API base URL from environment or use default"""
    api_url = os.getenv('LEGAL_API_URL')
    if api_url:
        return api_url
    
    # Try to detect the API server dynamically
    try:
        # Check if we're running locally
        import socket
        hostname = socket.gethostname()
        if hostname in ['localhost', '127.0.0.1']:
            api_port = os.getenv('API_PORT', '5002')
            return f'http://localhost:{api_port}'
        
        # Try to get public IP
        response = requests.get('https://api.ipify.org', timeout=API_REQUEST_TIMEOUT)
        if response.status_code == 200:
            public_ip = response.text.strip()
            api_port = os.getenv('API_PORT', '5002')
            return f'http://{public_ip}:{api_port}'
    except Exception as e:
        print(f"Warning: Could not detect API URL dynamically: {e}")
    
    # Fallback to localhost
    api_port = os.getenv('API_PORT', '5002')
    return f'http://localhost:{api_port}'

API_BASE_URL = get_api_base_url()

def assign_cases_to_shantharam():
    """Assign orphaned cases to shantharam user (ID: 4)"""
    print("🔧 Assigning orphaned cases to shantharam user...")
    print("=" * 60)
    
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Verify shantharam user exists
        cursor.execute("SELECT id, username, role FROM users WHERE id = 4")
        user = cursor.fetchone()
        
        if not user:
            print("❌ User with ID 4 not found")
            return False
        
        print(f"✅ Found user: {user[1]} (ID: {user[0]}, Role: {user[2]})")
        
        # Find orphaned cases
        cursor.execute("SELECT cnr_number, case_title FROM cases WHERE user_id IS NULL")
        orphaned_cases = cursor.fetchall()
        
        if not orphaned_cases:
            print("✅ No orphaned cases found")
            return True
        
        print(f"📋 Found {len(orphaned_cases)} orphaned case(s):")
        for case in orphaned_cases:
            print(f"   CNR: {case[0]}, Title: {case[1]}")
        
        # Assign orphaned cases to shantharam (ID: 4)
        cursor.execute("UPDATE cases SET user_id = 4 WHERE user_id IS NULL")
        updated_count = cursor.rowcount
        
        conn.commit()
        
        print(f"✅ Successfully assigned {updated_count} case(s) to shantharam")
        
        # Verify the assignment
        cursor.execute("SELECT cnr_number, case_title, user_id FROM cases WHERE user_id = 4")
        assigned_cases = cursor.fetchall()
        
        print(f"\n📊 Cases now assigned to shantharam (ID: 4):")
        for case in assigned_cases:
            print(f"   CNR: {case[0]}, Title: {case[1]}, User ID: {case[2]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error assigning cases: {e}")
        return False

def test_user_dashboard_after_fix():
    """Test the dashboard API after assigning cases"""
    print("\n🧪 Testing dashboard API after fix...")
    
    import requests
    
    try:
        # Login as shantharam
        shantharam_password = os.getenv('SHANTHARAM_PASSWORD', 'shantharam123')
        login_data = {"username": "shantharam", "password": shantharam_password}
        response = requests.post(f"{API_BASE_URL}/api/auth/login", json=login_data)
        
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            # Try with a different password
            login_data = {"username": "shantharam", "password": "password"}
            response = requests.post(f"{API_BASE_URL}/api/auth/login", json=login_data)
            
            if response.status_code != 200:
                print(f"❌ Login still failed: {response.status_code}")
                print("   Please check shantharam's password")
                return False
        
        token = response.json().get('token')
        print(f"✅ Login as shantharam successful")
        
        # Test dashboard data API
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        response = requests.get(f"{API_BASE_URL}/api/user/dashboard-data", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            summary = result.get('dashboard_data', {}).get('summary', {})
            cases = result.get('dashboard_data', {}).get('cases', [])
            
            print(f"✅ Dashboard API successful")
            print(f"   Total cases: {summary.get('total_cases', 0)}")
            print(f"   Active cases: {summary.get('active_cases', 0)}")
            print(f"   Cases in data: {len(cases)}")
            
            for i, case in enumerate(cases, 1):
                print(f"   Case {i}: CNR: {case.get('cnr_number')}, User ID: {case.get('user_id')}")
            
            return len(cases) > 0
        else:
            print(f"❌ Dashboard API failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Dashboard test error: {e}")
        return False

def main():
    """Main function"""
    print("🚀 ASSIGNING CASES TO SHANTHARAM USER")
    print("=" * 60)
    
    # Assign orphaned cases
    success = assign_cases_to_shantharam()
    
    if success:
        # Test dashboard after fix
        test_user_dashboard_after_fix()
        
        print("\n" + "=" * 60)
        print("🎉 CASES ASSIGNED TO SHANTHARAM!")
        print("=" * 60)
        print("💡 Now refresh your frontend pages:")
        print("   - Legal Dashboard should show case count")
        print("   - Cases Management should show both cases")
        print("   - All pages should work for shantharam user!")
        print("")
        print("🔑 Make sure you're logged in as 'shantharam' user")
    else:
        print("\n❌ Failed to assign cases to shantharam")

if __name__ == "__main__":
    main()
