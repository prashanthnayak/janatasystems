#!/usr/bin/env python3
"""
Quick script to check backend status and CORS
"""

import requests
import subprocess
import time

def check_backend():
    """Check if backend is running and accessible"""
    print("🔍 Checking backend status...")
    
    # Check if process is running
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        python_processes = [line for line in result.stdout.split('\n') if 'python' in line and 'legal_api' in line]
        
        if python_processes:
            print("✅ Backend process found:")
            for proc in python_processes:
                print(f"  {proc}")
        else:
            print("❌ No backend process found")
            print("Starting backend...")
            subprocess.Popen(['python3', 'legal_api.py'], cwd='/Users/prashanth/janatasystems')
            time.sleep(3)
    except Exception as e:
        print(f"Error checking processes: {e}")
    
    # Test localhost access
    print("\n🔍 Testing localhost:5002...")
    try:
        response = requests.get("http://localhost:5002/api/server-info", timeout=5)
        print(f"✅ Localhost response: {response.status_code}")
    except Exception as e:
        print(f"❌ Localhost failed: {e}")
    
    # Test external access
    print("\n🔍 Testing external access...")
    try:
        response = requests.get("http://18.234.219.146:5002/api/server-info", timeout=5)
        print(f"✅ External response: {response.status_code}")
    except Exception as e:
        print(f"❌ External failed: {e}")
    
    # Test CORS preflight
    print("\n🔍 Testing CORS preflight...")
    try:
        response = requests.options("http://18.234.219.146:5002/api/cases/save", timeout=5)
        print(f"CORS preflight response: {response.status_code}")
        print(f"CORS headers: {dict(response.headers)}")
    except Exception as e:
        print(f"❌ CORS test failed: {e}")

if __name__ == "__main__":
    check_backend()
