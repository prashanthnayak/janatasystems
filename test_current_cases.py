#!/usr/bin/env python3
"""
Quick test to check current cases in database
"""

import requests
import json

def test_current_cases():
    print("🔍 Checking current cases in database...")
    
    # Login first
    login_url = "http://18.234.219.146:5002/api/auth/login"
    login_data = {
        "username": "shantharam",
        "password": "shantharam123"
    }
    
    try:
        print("📝 Step 1: Login...")
        login_response = requests.post(login_url, json=login_data, timeout=10)
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            if login_result.get('success'):
                token = login_result.get('token')
                print(f"✅ Login successful! Token: {token[:20]}...")
                
                print("📝 Step 2: Check dashboard API...")
                headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
                
                dashboard_url = "http://18.234.219.146:5002/api/user/dashboard-data"
                dashboard_response = requests.get(dashboard_url, headers=headers, timeout=10)
                
                if dashboard_response.status_code == 200:
                    dashboard_result = dashboard_response.json()
                    print(f"✅ Dashboard API responded: {dashboard_response.status_code}")
                    
                    if dashboard_result.get('success'):
                        dashboard_data = dashboard_result.get('dashboard_data', {})
                        cases = dashboard_data.get('cases', [])
                        print(f"📊 Cases in dashboard: {len(cases)}")
                        
                        if cases:
                            print("✅ Cases found!")
                            for i, case in enumerate(cases):
                                print(f"  {i+1}. CNR: {case.get('cnr_number')}, Title: {case.get('case_title')}, User ID: {case.get('user_id')}")
                        else:
                            print("❌ No cases found in dashboard!")
                            
                        # Also check cases API directly
                        print("\n📝 Step 3: Check cases API directly...")
                        cases_url = "http://18.234.219.146:5002/api/cases"
                        cases_response = requests.get(cases_url, headers=headers, timeout=10)
                        
                        if cases_response.status_code == 200:
                            cases_result = cases_response.json()
                            if cases_result.get('success'):
                                cases_list = cases_result.get('cases', [])
                                print(f"📊 Cases in cases API: {len(cases_list)}")
                                
                                if cases_list:
                                    print("✅ Cases found in cases API!")
                                    for i, case in enumerate(cases_list):
                                        print(f"  {i+1}. CNR: {case.get('cnr_number')}, Title: {case.get('case_title')}, User ID: {case.get('user_id')}")
                                else:
                                    print("❌ No cases found in cases API!")
                            else:
                                print(f"❌ Cases API failed: {cases_result.get('error')}")
                        else:
                            print(f"❌ Cases API error: {cases_response.status_code}")
                            
                    else:
                        print(f"❌ Dashboard API failed: {dashboard_result.get('error')}")
                else:
                    print(f"❌ Dashboard API error: {dashboard_response.status_code}")
            else:
                print(f"❌ Login failed: {login_result.get('error')}")
        else:
            print(f"❌ Login request failed: {login_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")

if __name__ == "__main__":
    test_current_cases()
