#!/usr/bin/env python3
"""
Debug script to check user cases mismatch
"""

import requests
import json
import psycopg2

def debug_user_cases():
    """Debug user cases mismatch"""
    try:
        print("🔍 Debugging user cases mismatch...")
        
        # Step 1: Login and get token
        print("\n📝 Step 1: Login to get token...")
        login_data = {
            "username": "shantharam",
            "password": "password123"
        }
        
        login_response = requests.post("http://localhost:5002/api/auth/login", json=login_data)
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return
        
        login_result = login_response.json()
        token = login_result.get('token')
        user_info = login_result.get('user', {})
        user_id = user_info.get('id')
        username = user_info.get('username')
        
        print(f"✅ Login successful!")
        print(f"👤 User: {username} (ID: {user_id})")
        print(f"🎫 Token: {token[:20]}...")
        
        # Step 2: Check database directly
        print(f"\n📝 Step 2: Check database directly...")
        db_params = {
            'host': 'localhost',
            'database': 'legal_management',
            'user': 'prashanth',
            'password': 'secure_password_123',
            'port': '5432'
        }
        
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        # Get all cases with user_id
        cursor.execute("""
            SELECT cnr_number, case_title, client_name, user_id, created_at 
            FROM cases 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        all_cases = cursor.fetchall()
        
        print(f"📊 All cases in database: {len(all_cases)}")
        for case in all_cases:
            cnr, title, client, case_user_id, created = case
            print(f"  - CNR: {cnr}, Title: {title}, Client: {client}, User ID: {case_user_id}, Created: {created}")
        
        # Get cases for current user
        cursor.execute("""
            SELECT cnr_number, case_title, client_name, user_id, created_at 
            FROM cases 
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user_id,))
        user_cases = cursor.fetchall()
        
        print(f"📊 Cases for user {username} (ID: {user_id}): {len(user_cases)}")
        for case in user_cases:
            cnr, title, client, case_user_id, created = case
            print(f"  - CNR: {cnr}, Title: {title}, Client: {client}, User ID: {case_user_id}, Created: {created}")
        
        conn.close()
        
        # Step 3: Test dashboard API
        print(f"\n📝 Step 3: Test dashboard API...")
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        dashboard_response = requests.get("http://localhost:5002/api/user/dashboard-data", headers=headers)
        if dashboard_response.status_code == 200:
            dashboard_data = dashboard_response.json()
            dashboard_cases = dashboard_data.get('dashboard_data', {}).get('cases', [])
            print(f"📊 Dashboard API shows {len(dashboard_cases)} cases")
            
            if dashboard_cases:
                print("📋 Dashboard cases:")
                for case in dashboard_cases:
                    print(f"  - CNR: {case.get('cnr_number')}, Title: {case.get('case_title')}, User ID: {case.get('user_id')}")
            else:
                print("❌ Dashboard shows 0 cases")
        else:
            print(f"❌ Dashboard API failed: {dashboard_response.status_code}")
            print(f"Response: {dashboard_response.text}")
        
        # Step 4: Test cases API
        print(f"\n📝 Step 4: Test cases API...")
        cases_response = requests.get("http://localhost:5002/api/cases", headers=headers)
        if cases_response.status_code == 200:
            cases_data = cases_response.json()
            api_cases = cases_data.get('cases', [])
            print(f"📊 Cases API shows {len(api_cases)} cases")
            
            if api_cases:
                print("📋 Cases API cases:")
                for case in api_cases:
                    print(f"  - CNR: {case.get('cnr_number')}, Title: {case.get('case_title')}, User ID: {case.get('user_id')}")
            else:
                print("❌ Cases API shows 0 cases")
        else:
            print(f"❌ Cases API failed: {cases_response.status_code}")
            print(f"Response: {cases_response.text}")
        
        print(f"\n✅ Debug completed!")
        
    except Exception as e:
        print(f"❌ Error during debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_user_cases()
