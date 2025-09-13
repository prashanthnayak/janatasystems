#!/usr/bin/env python3
"""
Fix database table structure
Adds missing columns to case_history table
"""

from database_setup import DatabaseManager

def main():
    print("🔧 Fixing database table structure...")
    
    db = DatabaseManager()
    
    # Fix the case_history table
    if db.fix_case_history_table():
        print("✅ Database table structure fixed successfully!")
    else:
        print("❌ Failed to fix database table structure")
        return False
    
    return True

if __name__ == "__main__":
    main() 