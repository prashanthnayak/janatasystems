#!/usr/bin/env python3
"""
Test script to verify CORS fix is working
"""

import requests
import json

def test_cors_fix():
    """Test if CORS fix is working"""
    print("🔍 Testing CORS fix...")
    
    # Test OPTIONS request (CORS preflight)
    print("\n📝 Testing OPTIONS request...")
    try:
        response = requests.options(
            "http://18.234.219.146:5002/api/cases/save",
            headers={
                "Origin": "http://18.234.219.146:8000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,Authorization"
            }
        )
        
        print(f"OPTIONS Response Status: {response.status_code}")
        print(f"OPTIONS Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ OPTIONS request successful!")
        else:
            print(f"❌ OPTIONS request failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ OPTIONS request error: {e}")
    
    # Test POST request with authentication
    print("\n📝 Testing POST request...")
    try:
        # First login to get token
        login_response = requests.post("http://18.234.219.146:5002/api/auth/login", 
                                     json={"username": "shantharam", "password": "password123"})
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            if login_data.get('success'):
                token = login_data.get('token')
                print(f"✅ Login successful, token: {token[:20]}...")
                
                # Test POST request
                post_response = requests.post(
                    "http://18.234.219.146:5002/api/cases/save",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {token}",
                        "Origin": "http://18.234.219.146:8000"
                    },
                    json={
                        "cnr_number": "TEST_CORS_FIX",
                        "user_data": {
                            "case_title": "CORS Test Case",
                            "client_name": "CORS Test Client"
                        }
                    }
                )
                
                print(f"POST Response Status: {post_response.status_code}")
                print(f"POST Response: {post_response.text}")
                
                if post_response.status_code == 200:
                    print("✅ POST request successful!")
                else:
                    print(f"❌ POST request failed with status {post_response.status_code}")
            else:
                print(f"❌ Login failed: {login_data.get('error')}")
        else:
            print(f"❌ Login request failed: {login_response.status_code}")
            
    except Exception as e:
        print(f"❌ POST request error: {e}")

if __name__ == "__main__":
    test_cors_fix()
