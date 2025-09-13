#!/usr/bin/env python3
"""
Check if scraped data was saved to the database
"""

from database_setup import DatabaseManager

def main():
    print("🔍 Checking database for scraped data...")
    
    db = DatabaseManager()
    cnr_number = "KAUP050003552024"
    
    # Check if case exists
    print(f"\n📋 Checking case data for CNR: {cnr_number}")
    case = db.get_case(cnr_number)
    if case:
        print("✅ Case found in database:")
        for key, value in case.items():
            print(f"   {key}: {value}")
    else:
        print("❌ Case not found in database")
    
    # Check case history
    print(f"\n📜 Checking case history for CNR: {cnr_number}")
    try:
        conn = db.get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT judge, business_date, hearing_date, purpose, created_at 
                FROM case_history 
                WHERE cnr_number = %s 
                ORDER BY created_at DESC
            """, (cnr_number,))
            
            rows = cursor.fetchall()
            if rows:
                print(f"✅ Found {len(rows)} case history entries:")
                for i, row in enumerate(rows, 1):
                    print(f"   Entry {i}:")
                    print(f"     Judge: {row[0]}")
                    print(f"     Business Date: {row[1]}")
                    print(f"     Hearing Date: {row[2]}")
                    print(f"     Purpose: {row[3]}")
                    print(f"     Created: {row[4]}")
            else:
                print("❌ No case history entries found")
            
            conn.close()
        else:
            print("❌ Could not connect to database")
    except Exception as e:
        print(f"❌ Error checking case history: {e}")

if __name__ == "__main__":
    main() 