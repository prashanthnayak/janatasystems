#!/usr/bin/env python3
"""
Check what cases are saved in the database
"""

from database_setup import DatabaseManager

def check_saved_cases():
    """Check all cases in the database"""
    print("🔍 Checking saved cases in database...")
    print("=" * 50)
    
    try:
        # Initialize database manager
        db = DatabaseManager()
        
        # Get all cases
        cases = db.get_all_cases()
        
        if not cases:
            print("❌ No cases found in database")
            print("\n🔧 Possible reasons:")
            print("   1. Cases table is empty")
            print("   2. Database connection issue")
            print("   3. Cases were not saved properly")
            return
        
        print(f"✅ Found {len(cases)} case(s) in database:")
        print()
        
        for i, case in enumerate(cases, 1):
            print(f"📋 Case {i}:")
            print(f"   CNR: {case.get('cnr_number', 'N/A')}")
            print(f"   Title: {case.get('case_title', 'N/A')}")
            print(f"   Client: {case.get('client_name', 'N/A')}")
            print(f"   Type: {case.get('case_type', 'N/A')}")
            print(f"   Court: {case.get('court_name', 'N/A')}")
            print(f"   Status: {case.get('status', 'N/A')}")
            print(f"   User ID: {case.get('user_id', 'N/A')}")
            print(f"   Created: {case.get('created_at', 'N/A')}")
            print()
            
    except Exception as e:
        print(f"❌ Error checking cases: {e}")

def check_database_connection():
    """Test database connection"""
    print("🔗 Testing database connection...")
    
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        
        if conn:
            print("✅ Database connection successful")
            
            # Check if tables exist
            cursor = conn.cursor()
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('cases', 'case_history', 'users', 'user_sessions')
            """)
            
            tables = cursor.fetchall()
            print(f"📋 Found tables: {[table[0] for table in tables]}")
            
            # Check cases table structure
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'cases'
                ORDER BY ordinal_position
            """)
            
            columns = cursor.fetchall()
            print(f"📋 Cases table columns: {[(col[0], col[1]) for col in columns]}")
            
            conn.close()
        else:
            print("❌ Database connection failed")
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")

def check_user_sessions():
    """Check user sessions"""
    print("\n🔑 Checking user sessions...")
    
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT us.session_token, u.username, u.role, us.expires_at
                FROM user_sessions us
                JOIN users u ON us.user_id = u.id
                WHERE us.expires_at > NOW()
                ORDER BY us.created_at DESC
                LIMIT 5
            """)
            
            sessions = cursor.fetchall()
            
            if sessions:
                print(f"✅ Found {len(sessions)} active session(s):")
                for session in sessions:
                    token_preview = session[0][:20] + "..." if session[0] else "N/A"
                    print(f"   User: {session[1]} ({session[2]}) - Token: {token_preview}")
            else:
                print("❌ No active sessions found")
                print("   Users need to login to see their cases")
            
            conn.close()
            
    except Exception as e:
        print(f"❌ Error checking sessions: {e}")

if __name__ == "__main__":
    print("🚀 Starting database check...")
    print("=" * 60)
    
    # Test database connection
    check_database_connection()
    
    # Check saved cases
    print("\n" + "=" * 60)
    check_saved_cases()
    
    # Check user sessions
    check_user_sessions()
    
    print("=" * 60)
    print("🏁 Database check completed!")
    
    print("\n💡 If no cases are shown:")
    print("   1. Make sure you're logged in with the same user who saved the cases")
    print("   2. Check if cases are filtered by user_id")
    print("   3. Clear browser cache and try again")
    print("   4. Check browser console for API errors")
