#!/usr/bin/env python3
"""
Database Connection Diagnostic Script
Run this on EC2 to diagnose database connection issues
"""

import psycopg2
import socket
import sys

def test_network_connectivity():
    """Test if we can reach the database server"""
    print("🔍 Testing network connectivity to database server...")
    
    host = "52.23.206.51"
    port = 5432
    
    try:
        # Test if port is open
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)  # 5 second timeout
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Port {port} is open on {host}")
            return True
        else:
            print(f"❌ Cannot connect to {host}:{port} - Connection refused")
            return False
            
    except Exception as e:
        print(f"❌ Network error: {e}")
        return False

def test_database_connection():
    """Test database connection with credentials"""
    print("\n🔍 Testing database connection with credentials...")
    
    db_params = {
        'host': '52.23.206.51',
        'database': 'legal_management',
        'user': 'prashanth',
        'password': 'secure_password_123',
        'port': '5432'
    }
    
    try:
        conn = psycopg2.connect(**db_params)
        print("✅ Database connection successful!")
        
        # Test a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"📊 PostgreSQL version: {version[0]}")
        
        # Check if users table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            );
        """)
        table_exists = cursor.fetchone()[0]
        print(f"👥 Users table exists: {table_exists}")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def suggest_solutions():
    """Suggest solutions based on the test results"""
    print("\n🔧 SUGGESTED SOLUTIONS:")
    print("=" * 50)
    
    print("1. CHECK POSTGRESQL SERVICE:")
    print("   sudo systemctl status postgresql")
    print("   sudo systemctl start postgresql")
    print("")
    
    print("2. CHECK POSTGRESQL CONFIGURATION:")
    print("   sudo nano /etc/postgresql/*/main/postgresql.conf")
    print("   Ensure: listen_addresses = '*'")
    print("")
    
    print("3. CHECK PG_HBA.CONF:")
    print("   sudo nano /etc/postgresql/*/main/pg_hba.conf")
    print("   Add: host all all 0.0.0.0/0 md5")
    print("")
    
    print("4. CHECK FIREWALL:")
    print("   sudo ufw status")
    print("   sudo ufw allow 5432")
    print("")
    
    print("5. RESTART POSTGRESQL:")
    print("   sudo systemctl restart postgresql")

def main():
    print("🩺 DATABASE CONNECTION DIAGNOSTIC")
    print("=" * 40)
    
    # Test 1: Network connectivity
    network_ok = test_network_connectivity()
    
    # Test 2: Database connection
    db_ok = test_database_connection()
    
    # Results
    print("\n📋 DIAGNOSTIC RESULTS:")
    print("=" * 25)
    print(f"Network connectivity: {'✅ OK' if network_ok else '❌ FAILED'}")
    print(f"Database connection: {'✅ OK' if db_ok else '❌ FAILED'}")
    
    if not network_ok or not db_ok:
        suggest_solutions()
    else:
        print("\n🎉 Database is working correctly!")
        print("The issue might be elsewhere in your application.")

if __name__ == "__main__":
    main()