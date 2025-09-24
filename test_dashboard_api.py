#!/usr/bin/env python3
"""
Test script to test the dashboard API endpoint
Run this on EC2 to test the /api/user/dashboard-data endpoint
"""

import requests
import json

def test_dashboard_api():
    """Test the dashboard API endpoint"""
    try:
        # Get a valid token first (you'll need to login and get this)
        print("🔍 Testing dashboard API endpoint...")
        
        # You need to replace this with a valid token from your login
        token = "YOUR_TOKEN_HERE"  # Replace with actual token
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Test the dashboard API
        url = "http://localhost:5002/api/user/dashboard-data"
        print(f"🚀 Calling: {url}")
        
        response = requests.get(url, headers=headers)
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Response:")
            print(f"  Success: {data.get('success')}")
            
            if data.get('success'):
                dashboard_data = data.get('dashboard_data', {})
                cases = dashboard_data.get('cases', [])
                clients = dashboard_data.get('clients', [])
                events = dashboard_data.get('calendar_events', [])
                
                print(f"📊 Dashboard Data:")
                print(f"  Cases: {len(cases)}")
                print(f"  Clients: {len(clients)}")
                print(f"  Calendar Events: {len(events)}")
                
                if cases:
                    print(f"📋 First case: {cases[0]}")
                else:
                    print("❌ No cases returned")
                    
            else:
                print(f"❌ API Error: {data.get('error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")

if __name__ == "__main__":
    print("🔍 Testing dashboard API...")
    print("⚠️ Note: You need to replace 'YOUR_TOKEN_HERE' with a valid login token")
    test_dashboard_api()
