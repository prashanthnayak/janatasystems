#!/usr/bin/env python3
"""
Test script to check database on EC2
Run this on EC2 to see what's in the database
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os

def test_ec2_database():
    """Test database connection on EC2"""
    try:
        # Database connection parameters (same as in database_setup.py)
        db_params = {
            'host': 'localhost',
            'database': 'legal_management', 
            'user': 'prashanth',
            'password': 'secure_password_123',
            'port': '5432'
        }
        
        print("🔍 Connecting to PostgreSQL database on EC2...")
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        print("✅ Connected to database successfully!")
        
        # Check if cases table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'cases'
            );
        """)
        table_exists = cursor.fetchone()[0]
        print(f"📋 Cases table exists: {table_exists}")
        
        if table_exists:
            # Count total cases
            cursor.execute("SELECT COUNT(*) FROM cases")
            total_cases = cursor.fetchone()[0]
            print(f"📊 Total cases in database: {total_cases}")
            
            # Show all cases with user_id
            cursor.execute("""
                SELECT cnr_number, case_title, client_name, user_id, created_at 
                FROM cases 
                ORDER BY created_at DESC 
                LIMIT 10
            """)
            cases = cursor.fetchall()
            
            if cases:
                print("📋 Recent cases:")
                for case in cases:
                    cnr, title, client, user_id, created = case
                    print(f"  - CNR: {cnr}, Title: {title}, Client: {client}, User ID: {user_id}, Created: {created}")
            else:
                print("❌ No cases found in database")
            
            # Check for cases with NULL user_id
            cursor.execute("SELECT COUNT(*) FROM cases WHERE user_id IS NULL")
            null_user_cases = cursor.fetchone()[0]
            print(f"⚠️ Cases with NULL user_id: {null_user_cases}")
            
            # Check users table
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users'
                );
            """)
            users_table_exists = cursor.fetchone()[0]
            print(f"👥 Users table exists: {users_table_exists}")
            
            if users_table_exists:
                cursor.execute("SELECT id, username, role FROM users ORDER BY id")
                users = cursor.fetchall()
                print(f"👥 Users in database: {len(users)}")
                for user in users:
                    user_id, username, role = user
                    print(f"  - ID: {user_id}, Username: {username}, Role: {role}")
        
        conn.close()
        print("✅ Database test completed")
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    print("🔍 Testing EC2 database connection and data...")
    test_ec2_database()
