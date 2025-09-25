#!/usr/bin/env python3
"""
Simple script to get authentication token for testing
Run this on EC2 to get a valid token
"""

import requests
import json

def get_token():
    """Get authentication token for testing"""
    try:
        print("🔍 Getting authentication token...")
        
        # Login data - use one of these existing users:
        login_options = [
            {"username": "admin", "password": "password123", "role": "admin"},
            {"username": "shantharam", "password": "password123", "role": "user"},
            {"username": "kjkjhkh", "password": "password123", "role": "user"},
            {"username": "rohit", "password": "password123", "role": "user"}
        ]
        
        print("Available users:")
        for i, user in enumerate(login_options, 1):
            print(f"  {i}. {user['username']} ({user['role']})")
        
        # Use shantharam by default (or you can change this)
        login_data = {
            "username": "shantharam",  # Change this to any user you want
            "password": "password123"
        }
        
        print(f"\n🔑 Logging in as: {login_data['username']}")
        
        # Make login request
        response = requests.post("http://localhost:5002/api/auth/login", json=login_data)
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                token = result.get('token')
                user_info = result.get('user', {})
                
                print(f"✅ Login successful!")
                print(f"👤 User: {user_info.get('username')} (ID: {user_info.get('id')})")
                print(f"🎫 Token: {token}")
                print(f"\n📋 Copy this token for testing:")
                print(f"Bearer {token}")
                
                return token
            else:
                print(f"❌ Login failed: {result.get('error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    get_token()
