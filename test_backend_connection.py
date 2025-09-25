#!/usr/bin/env python3
"""
Test script to check if backend is running and accessible
Run this on EC2 to test backend connectivity
"""

import requests
import json

def test_backend_connection():
    """Test backend connectivity"""
    try:
        print("🔍 Testing backend connection...")
        
        # Test 1: Check if backend is running
        print("\n📝 Test 1: Check if backend is running...")
        try:
            response = requests.get("http://localhost:5002/api/server-info", timeout=5)
            print(f"Server info response: {response.status_code}")
            if response.status_code == 200:
                print("✅ Backend is running!")
                print(f"Response: {response.json()}")
            else:
                print(f"⚠️ Backend responded with status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("❌ Backend is NOT running on localhost:5002")
            return False
        except Exception as e:
            print(f"❌ Error connecting to backend: {e}")
            return False
        
        # Test 2: Check external access
        print("\n📝 Test 2: Check external access...")
        try:
            response = requests.get("http://18.234.219.146:5002/api/server-info", timeout=5)
            print(f"External access response: {response.status_code}")
            if response.status_code == 200:
                print("✅ Backend is accessible externally!")
            else:
                print(f"⚠️ External access responded with status: {response.status_code}")
        except Exception as e:
            print(f"❌ External access failed: {e}")
        
        # Test 3: Check CORS headers
        print("\n📝 Test 3: Check CORS headers...")
        try:
            response = requests.options("http://localhost:5002/api/cases/save", timeout=5)
            print(f"CORS preflight response: {response.status_code}")
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            print(f"CORS headers: {cors_headers}")
            
            if response.headers.get('Access-Control-Allow-Origin') == '*':
                print("✅ CORS is configured correctly")
            else:
                print("⚠️ CORS might not be configured properly")
                
        except Exception as e:
            print(f"❌ CORS test failed: {e}")
        
        # Test 4: Check if backend process is running
        print("\n📝 Test 4: Check backend process...")
        import subprocess
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            if 'python' in result.stdout and '5002' in result.stdout:
                print("✅ Backend process is running")
                # Show the process
                for line in result.stdout.split('\n'):
                    if 'python' in line and '5002' in line:
                        print(f"Process: {line}")
            else:
                print("❌ Backend process not found")
        except Exception as e:
            print(f"❌ Could not check processes: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during connection test: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing backend connection...")
    test_backend_connection()
