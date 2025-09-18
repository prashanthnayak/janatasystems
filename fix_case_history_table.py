#!/usr/bin/env python3
"""
Fix case_history table by adding missing status column
"""

from database_setup import DatabaseManager

def fix_case_history_table():
    """Add missing status column to case_history table"""
    print("🔧 Fixing case_history table...")
    
    try:
        # Initialize database manager
        db = DatabaseManager()
        
        # Add the missing status column
        success = db.add_status_column_to_case_history()
        
        if success:
            print("✅ case_history table fixed successfully!")
            print("   The 'status' column has been added.")
        else:
            print("❌ Failed to fix case_history table")
            
    except Exception as e:
        print(f"❌ Error fixing case_history table: {e}")

def test_case_history_insert():
    """Test inserting a record into case_history table"""
    print("\n🧪 Testing case_history insert...")
    
    try:
        db = DatabaseManager()
        
        # Test insert with sample data
        success = db.insert_case_history(
            cnr_number="TEST123",
            judge="Test Judge",
            business_date="2024-01-01",
            hearing_date="2024-01-15",
            purpose="Test Purpose",
            status="Active",
            user_id=1
        )
        
        if success:
            print("✅ Test insert successful!")
        else:
            print("❌ Test insert failed")
            
    except Exception as e:
        print(f"❌ Test insert error: {e}")

if __name__ == "__main__":
    print("🚀 Starting case_history table fix...")
    print("=" * 50)
    
    # Fix the table
    fix_case_history_table()
    
    # Test the fix
    test_case_history_insert()
    
    print("=" * 50)
    print("🏁 case_history table fix completed!")
    print("\n💡 Now try saving a case again - it should work!")
