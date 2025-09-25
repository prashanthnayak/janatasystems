#!/usr/bin/env python3
"""
Debug script to check backend startup and errors
"""

import subprocess
import time
import os

def debug_backend():
    """Debug backend startup issues"""
    print("🔍 Debugging backend startup...")
    
    # Kill any existing processes
    print("🛑 Killing existing backend processes...")
    subprocess.run(['sudo', 'pkill', '-f', 'python.*legal_api.py'], capture_output=True)
    time.sleep(2)
    
    # Check if legal_api.py exists
    if not os.path.exists('legal_api.py'):
        print("❌ legal_api.py not found in current directory")
        print("Current directory:", os.getcwd())
        print("Files in current directory:", os.listdir('.'))
        return
    
    print("✅ legal_api.py found")
    
    # Try to start backend and capture output
    print("🚀 Starting backend with error capture...")
    try:
        # Start backend and capture both stdout and stderr
        process = subprocess.Popen(
            ['python3', 'legal_api.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Read output for a few seconds
        print("📋 Backend output:")
        for i in range(10):  # Read for 10 seconds
            try:
                output = process.stdout.readline()
                if output:
                    print(f"  {output.strip()}")
                else:
                    break
                time.sleep(1)
            except:
                break
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Backend started successfully")
            print("🔍 Testing connectivity...")
            time.sleep(2)
            
            # Test connectivity
            import requests
            try:
                response = requests.get("http://localhost:5002/api/server-info", timeout=5)
                print(f"✅ Backend responding: {response.status_code}")
            except Exception as e:
                print(f"❌ Backend not responding: {e}")
        else:
            print("❌ Backend process died")
            print(f"Exit code: {process.poll()}")
            
    except Exception as e:
        print(f"❌ Error starting backend: {e}")

if __name__ == "__main__":
    debug_backend()
