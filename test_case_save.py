#!/usr/bin/env python3
"""
Test script to test case saving process step by step
Run this on EC2 to debug why cases are not being saved
"""

import requests
import json
import psycopg2
from psycopg2.extras import RealDictCursor

def test_case_save_process():
    """Test the complete case saving process"""
    try:
        print("🔍 Testing case save process step by step...")
        
        # Step 1: Login and get token
        print("\n📝 Step 1: Login to get token...")
        login_data = {
            "username": "shantharam",  # Use existing user
            "password": "password123"  # Default password
        }
        
        login_response = requests.post("http://localhost:5002/api/login", json=login_data)
        print(f"Login response status: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return
        
        login_result = login_response.json()
        if not login_result.get('success'):
            print(f"❌ Login failed: {login_result.get('error')}")
            return
        
        token = login_result.get('token')
        user_id = login_result.get('user', {}).get('id')
        print(f"✅ Login successful! Token: {token[:20]}..., User ID: {user_id}")
        
        # Step 2: Test case save API
        print(f"\n📝 Step 2: Test case save API...")
        case_data = {
            "cnr_number": "TEST123456789",
            "user_data": {
                "case_title": "Test Case",
                "client_name": "Test Client",
                "client_phone": "9876543210",
                "client_email": "test@example.com",
                "case_type": "Civil",
                "court_name": "Test Court",
                "filing_date": "2024-01-01",
                "case_description": "This is a test case"
            }
        }
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        save_response = requests.post("http://localhost:5002/api/cases/save", 
                                    json=case_data, headers=headers)
        print(f"Save response status: {save_response.status_code}")
        print(f"Save response: {save_response.text}")
        
        # Step 3: Check if case was actually saved to database
        print(f"\n📝 Step 3: Check database directly...")
        db_params = {
            'host': 'localhost',
            'database': 'legal_management',
            'user': 'prashanth',
            'password': 'secure_password_123',
            'port': '5432'
        }
        
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        # Check if case exists
        cursor.execute("SELECT COUNT(*) FROM cases WHERE cnr_number = %s", ("TEST123456789",))
        case_count = cursor.fetchone()[0]
        print(f"Cases with CNR TEST123456789: {case_count}")
        
        if case_count > 0:
            cursor.execute("SELECT * FROM cases WHERE cnr_number = %s", ("TEST123456789",))
            case = cursor.fetchone()
            print(f"✅ Case found in database: {case}")
        else:
            print("❌ Case NOT found in database")
        
        conn.close()
        
        # Step 4: Test dashboard API
        print(f"\n📝 Step 4: Test dashboard API...")
        dashboard_response = requests.get("http://localhost:5002/api/user/dashboard-data", 
                                        headers=headers)
        print(f"Dashboard response status: {dashboard_response.status_code}")
        
        if dashboard_response.status_code == 200:
            dashboard_data = dashboard_response.json()
            cases = dashboard_data.get('dashboard_data', {}).get('cases', [])
            print(f"Dashboard shows {len(cases)} cases")
            
            if cases:
                print(f"✅ Dashboard shows cases: {cases[0]}")
            else:
                print("❌ Dashboard shows 0 cases")
        else:
            print(f"❌ Dashboard API failed: {dashboard_response.text}")
        
        print(f"\n✅ Test completed!")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔍 Testing case save process...")
    test_case_save_process()
