#!/usr/bin/env python3
"""
Test dashboard API directly to see why it's returning 0 cases
"""

import requests
import json

def test_dashboard_api():
    print("🔍 Testing dashboard API directly...")
    
    # Test the dashboard API endpoint
    dashboard_url = "http://18.234.219.146:5002/api/user/dashboard-data"
    
    # We need a valid token - let's try to get one
    login_url = "http://18.234.219.146:5002/api/auth/login"
    login_data = {
        "username": "shantharam",
        "password": "shantharam123"
    }
    
    try:
        print("📝 Step 1: Login to get token...")
        login_response = requests.post(login_url, json=login_data, timeout=10)
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            if login_result.get('success'):
                token = login_result.get('token')
                print(f"✅ Login successful! Token: {token[:20]}...")
                
                print("📝 Step 2: Test dashboard API...")
                headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
                
                dashboard_response = requests.get(dashboard_url, headers=headers, timeout=10)
                
                if dashboard_response.status_code == 200:
                    dashboard_result = dashboard_response.json()
                    print(f"✅ Dashboard API responded: {dashboard_response.status_code}")
                    print(f"Success: {dashboard_result.get('success')}")
                    
                    if dashboard_result.get('success'):
                        dashboard_data = dashboard_result.get('dashboard_data', {})
                        cases = dashboard_data.get('cases', [])
                        print(f"Cases: {len(cases)}")
                        
                        if cases:
                            print("✅ Cases found!")
                            for i, case in enumerate(cases[:3]):  # Show first 3 cases
                                print(f"  {i+1}. CNR: {case.get('cnr_number')}, Title: {case.get('case_title')}, User ID: {case.get('user_id')}")
                        else:
                            print("❌ No cases found!")
                            
                        # Show raw response
                        print(f"\nRaw Dashboard Data:")
                        print(json.dumps(dashboard_result, indent=2)[:1000] + "...")
                    else:
                        print(f"❌ Dashboard API failed: {dashboard_result.get('error')}")
                else:
                    print(f"❌ Dashboard API error: {dashboard_response.status_code}")
                    print(f"Response: {dashboard_response.text}")
            else:
                print(f"❌ Login failed: {login_result.get('error')}")
        else:
            print(f"❌ Login request failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")

if __name__ == "__main__":
    test_dashboard_api()
