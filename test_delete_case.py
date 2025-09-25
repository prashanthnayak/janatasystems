#!/usr/bin/env python3
"""
Test script to test delete case functionality
"""

import requests
import json

def test_delete_case():
    """Test delete case functionality"""
    try:
        print("🔍 Testing delete case functionality...")
        
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
        print(f"✅ Login successful! Token: {token[:20]}...")
        
        # Step 2: Get list of cases
        print("\n📝 Step 2: Get list of cases...")
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        cases_response = requests.get("http://localhost:5002/api/cases", headers=headers)
        if cases_response.status_code != 200:
            print(f"❌ Failed to get cases: {cases_response.text}")
            return
        
        cases_result = cases_response.json()
        cases = cases_result.get('cases', [])
        print(f"📊 Found {len(cases)} cases")
        
        if not cases:
            print("❌ No cases to delete")
            return
        
        # Step 3: Delete first case
        first_case = cases[0]
        cnr_number = first_case['cnr_number']
        print(f"\n📝 Step 3: Deleting case {cnr_number}...")
        
        delete_response = requests.delete(f"http://localhost:5002/api/cases/{cnr_number}", headers=headers)
        print(f"Delete response status: {delete_response.status_code}")
        print(f"Delete response: {delete_response.text}")
        
        # Step 4: Verify deletion
        print(f"\n📝 Step 4: Verifying deletion...")
        verify_response = requests.get("http://localhost:5002/api/cases", headers=headers)
        if verify_response.status_code == 200:
            verify_result = verify_response.json()
            remaining_cases = verify_result.get('cases', [])
            print(f"📊 Remaining cases: {len(remaining_cases)}")
            
            if len(remaining_cases) < len(cases):
                print("✅ Case deleted successfully!")
            else:
                print("❌ Case was not deleted")
        else:
            print(f"❌ Failed to verify deletion: {verify_response.text}")
        
        # Step 5: Test dashboard API
        print(f"\n📝 Step 5: Testing dashboard API...")
        dashboard_response = requests.get("http://localhost:5002/api/user/dashboard-data", headers=headers)
        if dashboard_response.status_code == 200:
            dashboard_data = dashboard_response.json()
            dashboard_cases = dashboard_data.get('dashboard_data', {}).get('cases', [])
            print(f"📊 Dashboard shows {len(dashboard_cases)} cases")
        else:
            print(f"❌ Dashboard API failed: {dashboard_response.text}")
        
        print(f"\n✅ Delete test completed!")
        
    except Exception as e:
        print(f"❌ Error during delete test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_delete_case()
