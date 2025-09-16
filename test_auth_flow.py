#!/usr/bin/env python3
"""
Test the authentication flow to debug 401 errors
"""

import requests
import json

def test_auth_flow():
    """Test the complete authentication flow"""
    
    base_url = "http://localhost:5002/api"
    
    print("🧪 Testing Authentication Flow")
    print("=" * 50)
    
    # Step 1: Test server connectivity
    print("\n1. Testing server connectivity...")
    try:
        response = requests.get(f"{base_url}/server-info")
        print(f"✅ Server is accessible: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return False
    
    # Step 2: Test login
    print("\n2. Testing login...")
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(f"{base_url}/auth/login", json=login_data)
        print(f"   Login status: {response.status_code}")
        
        if response.status_code == 200:
            login_result = response.json()
            print(f"✅ Login successful")
            print(f"   Token: {login_result.get('token', 'N/A')[:20]}...")
            print(f"   User: {login_result.get('user', {}).get('username', 'N/A')}")
            
            token = login_result.get('token')
            if not token:
                print("❌ No token received from login")
                return False
                
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Step 3: Test token validation
    print("\n3. Testing token validation...")
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Try a simple authenticated endpoint
        response = requests.get(f"{base_url}/server-info", headers=headers)
        print(f"   Token validation status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Token validation successful")
        else:
            print(f"❌ Token validation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Token validation error: {e}")
    
    # Step 4: Test save case endpoint
    print("\n4. Testing save case endpoint...")
    try:
        case_data = {
            "cnr_number": "TEST123",
            "user_data": {
                "case_title": "Test Case",
                "client_name": "Test Client",
                "case_type": "Civil",
                "court_name": "Test Court"
            }
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(f"{base_url}/cases/save", json=case_data, headers=headers)
        print(f"   Save case status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Save case successful")
            print(f"   Response: {result}")
        else:
            print(f"❌ Save case failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Save case error: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Authentication flow test completed")

if __name__ == "__main__":
    test_auth_flow()
