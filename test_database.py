#!/usr/bin/env python3
"""
Quick database test to check if cases are being saved
"""

import sqlite3
import os
import sys

def test_database():
    """Test database connection and check cases"""
    try:
        # Check if database file exists
        db_path = 'legal_cases.db'
        if not os.path.exists(db_path):
            print(f"❌ Database file not found: {db_path}")
            return False
        
        print(f"✅ Database file exists: {db_path}")
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if cases table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cases'")
        if not cursor.fetchone():
            print("❌ Cases table not found")
            return False
        
        print("✅ Cases table exists")
        
        # Count total cases
        cursor.execute("SELECT COUNT(*) FROM cases")
        total_cases = cursor.fetchone()[0]
        print(f"📊 Total cases in database: {total_cases}")
        
        # Show all cases
        cursor.execute("SELECT cnr_number, case_title, client_name, user_id FROM cases LIMIT 10")
        cases = cursor.fetchall()
        
        if cases:
            print("📋 Recent cases:")
            for case in cases:
                cnr, title, client, user_id = case
                print(f"  - CNR: {cnr}, Title: {title}, Client: {client}, User ID: {user_id}")
        else:
            print("❌ No cases found in database")
        
        # Check users table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cursor.fetchone():
            cursor.execute("SELECT id, username, role FROM users")
            users = cursor.fetchall()
            print(f"👥 Users in database: {len(users)}")
            for user in users:
                user_id, username, role = user
                print(f"  - ID: {user_id}, Username: {username}, Role: {role}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing database connection and data...")
    test_database()
