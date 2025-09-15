#!/usr/bin/env python3
"""
Database Migration Script
Run this on EC2 to ensure the database schema is correct for user creation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_setup import DatabaseManager

def main():
    print("🔄 Starting database migration...")
    
    db = DatabaseManager()
    
    # Test connection first
    conn = db.get_connection()
    if not conn:
        print("❌ Cannot connect to database. Check your connection.")
        return False
    
    print("✅ Database connection successful")
    conn.close()
    
    # Add phone column if it doesn't exist
    print("📞 Adding phone column to users table...")
    if db.add_phone_column_to_users():
        print("✅ Phone column migration completed")
    else:
        print("❌ Phone column migration failed")
        return False
    
    # Verify schema
    print("🔍 Verifying database schema...")
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check users table structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print("\n📋 Users table schema:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error verifying schema: {e}")
        return False
    
    print("\n✅ Database migration completed successfully!")
    print("🚀 User creation should now work properly.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
