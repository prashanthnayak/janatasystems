#!/usr/bin/env python3
"""
Test script to debug case deletion functionality
"""

import requests
import json
from database_setup import DatabaseManager

def test_delete_case():
    """Test case deletion from backend"""
    
    # First, let's check what cases exist
    print("🔍 Checking existing cases in database...")
    db = DatabaseManager()
    cases = db.get_all_cases()
    
    if not cases:
        print("❌ No cases found in database")
        return
    
    print(f"✅ Found {len(cases)} cases:")
    for case in cases[:5]:  # Show first 5
        print(f"  - {case['cnr_number']}: {case.get('case_title', 'No title')} (user_id: {case.get('user_id')})")
    
    # Test case to delete (use first case)
    test_cnr = cases[0]['cnr_number']
    print(f"\n🧪 Testing deletion of case: {test_cnr}")
    
    # Test 1: Direct database deletion
    print("\n1️⃣ Testing direct database deletion...")
    try:
        success = db.delete_case(test_cnr)
        if success:
            print("✅ Direct database deletion: SUCCESS")
        else:
            print("❌ Direct database deletion: FAILED")
    except Exception as e:
        print(f"❌ Direct database deletion error: {e}")
    
    # Test 2: API endpoint test (if we have a token)
    print("\n2️⃣ Testing API endpoint...")
    
    # Check if API server is running
    try:
        response = requests.get('http://localhost:5002/api/server-info', timeout=5)
        if response.status_code == 200:
            print("✅ API server is running")
            server_info = response.json()
            print(f"   Server: {server_info}")
        else:
            print(f"⚠️ API server responded with status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to API server: {e}")
        return
    
    # For API testing, we need a valid token
    print("\n3️⃣ Checking user sessions...")
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT token, user_id, username FROM user_sessions ORDER BY created_at DESC LIMIT 5")
        sessions = cursor.fetchall()
        conn.close()
        
        if sessions:
            print(f"✅ Found {len(sessions)} active sessions:")
            for session in sessions:
                token, user_id, username = session
                print(f"   - User {user_id} ({username}): {token[:20]}...")
                
                # Test API delete with this token
                print(f"\n🔥 Testing API DELETE with user {username}...")
                
                # First get another case to delete (since we may have deleted the first one)
                remaining_cases = db.get_all_cases()
                if not remaining_cases:
                    print("❌ No cases left to test API deletion")
                    continue
                    
                test_cnr_api = remaining_cases[0]['cnr_number']
                print(f"   Deleting case: {test_cnr_api}")
                
                headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
                
                try:
                    delete_response = requests.delete(
                        f'http://localhost:5002/api/cases/{test_cnr_api}',
                        headers=headers,
                        timeout=10
                    )
                    
                    print(f"   Status Code: {delete_response.status_code}")
                    print(f"   Response: {delete_response.text}")
                    
                    if delete_response.status_code == 200:
                        result = delete_response.json()
                        if result.get('success'):
                            print("✅ API deletion: SUCCESS")
                        else:
                            print(f"❌ API deletion failed: {result.get('error')}")
                    else:
                        print(f"❌ API deletion failed with status: {delete_response.status_code}")
                        
                except requests.exceptions.RequestException as e:
                    print(f"❌ API request failed: {e}")
                
                break  # Only test with first session
        else:
            print("❌ No active sessions found")
            
    except Exception as e:
        print(f"❌ Error checking sessions: {e}")

if __name__ == "__main__":
    test_delete_case()
