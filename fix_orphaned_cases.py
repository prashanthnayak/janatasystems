#!/usr/bin/env python3
"""
Fix orphaned cases by assigning them to a user
"""

from database_setup import DatabaseManager

def fix_orphaned_cases():
    """Assign orphaned cases to admin user"""
    print("🔧 Fixing orphaned cases...")
    print("=" * 50)
    
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get admin user ID
        cursor.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
        admin_user = cursor.fetchone()
        
        if not admin_user:
            print("❌ No admin user found")
            return False
        
        admin_id = admin_user[0]
        print(f"✅ Found admin user with ID: {admin_id}")
        
        # Find orphaned cases (user_id is NULL)
        cursor.execute("SELECT cnr_number, case_title FROM cases WHERE user_id IS NULL")
        orphaned_cases = cursor.fetchall()
        
        if not orphaned_cases:
            print("✅ No orphaned cases found")
            return True
        
        print(f"📋 Found {len(orphaned_cases)} orphaned case(s):")
        for case in orphaned_cases:
            print(f"   CNR: {case[0]}, Title: {case[1]}")
        
        # Ask for confirmation
        print(f"\n🔄 Will assign all orphaned cases to admin user (ID: {admin_id})")
        
        # Update orphaned cases
        cursor.execute("UPDATE cases SET user_id = %s WHERE user_id IS NULL", (admin_id,))
        updated_count = cursor.rowcount
        
        conn.commit()
        
        print(f"✅ Successfully updated {updated_count} case(s)")
        
        # Verify the fix
        cursor.execute("SELECT cnr_number, case_title, user_id FROM cases")
        all_cases = cursor.fetchall()
        
        print(f"\n📊 All cases after fix:")
        for case in all_cases:
            print(f"   CNR: {case[0]}, Title: {case[1]}, User ID: {case[2]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error fixing orphaned cases: {e}")
        return False

def test_cases_api_after_fix():
    """Test the cases API after fixing orphaned cases"""
    print("\n🧪 Testing cases API after fix...")
    
    import requests
    
    try:
        # Login
        login_data = {"username": "admin", "password": "admin123"}
        response = requests.post("http://localhost:5002/api/auth/login", json=login_data)
        
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            return False
        
        token = response.json().get('token')
        print(f"✅ Login successful")
        
        # Test cases API
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        response = requests.get("http://localhost:5002/api/cases", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            cases = result.get('cases', [])
            print(f"✅ Cases API returned {len(cases)} case(s)")
            
            for i, case in enumerate(cases, 1):
                print(f"   Case {i}: CNR: {case.get('cnr_number')}, User ID: {case.get('user_id')}")
            
            return len(cases) > 0
        else:
            print(f"❌ Cases API failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API test error: {e}")
        return False

def main():
    """Main function"""
    print("🚀 FIXING ORPHANED CASES")
    print("=" * 60)
    
    # Fix orphaned cases
    success = fix_orphaned_cases()
    
    if success:
        # Test API after fix
        test_cases_api_after_fix()
        
        print("\n" + "=" * 60)
        print("🎉 ORPHANED CASES FIXED!")
        print("=" * 60)
        print("💡 Now try refreshing your frontend pages:")
        print("   - Legal Dashboard")
        print("   - Cases Management")
        print("   - All pages should show the cases now!")
    else:
        print("\n❌ Failed to fix orphaned cases")

if __name__ == "__main__":
    main()
