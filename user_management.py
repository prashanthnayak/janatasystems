#!/usr/bin/env python3
"""
User Management Script for Legal System
Manages users, roles, and authentication
"""

from database_setup import DatabaseManager
import hashlib
import secrets
import datetime

class UserManager:
    def __init__(self):
        self.db = DatabaseManager()
    
    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username, email, password, full_name, role='user'):
        """Create a new user"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Hash the password
            password_hash = self.hash_password(password)
            
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, full_name, role, is_active)
                VALUES (%s, %s, %s, %s, %s, true)
                ON CONFLICT (username) DO UPDATE SET
                    email = EXCLUDED.email,
                    password_hash = EXCLUDED.password_hash,
                    full_name = EXCLUDED.full_name,
                    role = EXCLUDED.role,
                    is_active = EXCLUDED.is_active
            """, (username, email, password_hash, full_name, role))
            
            conn.commit()
            print(f"✅ User '{username}' created/updated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error creating user '{username}': {e}")
            conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    def list_users(self):
        """List all users"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT username, email, full_name, role, is_active, created_at, last_login
                FROM users ORDER BY role, username
            """)
            
            users = cursor.fetchall()
            
            print("\n" + "="*80)
            print("👥 USER MANAGEMENT SYSTEM")
            print("="*80)
            
            for user in users:
                username, email, full_name, role, is_active, created_at, last_login = user
                
                # Status and role icons
                status = "🟢 ACTIVE" if is_active else "🔴 INACTIVE"
                role_icon = "👑" if role == 'admin' else "👤"
                
                print(f"\n{role_icon} {username.upper()}")
                print(f"   📧 Email: {email}")
                print(f"   👤 Full Name: {full_name}")
                print(f"   🏷️  Role: {role.upper()}")
                print(f"   📊 Status: {status}")
                print(f"   📅 Created: {created_at}")
                if last_login:
                    print(f"   🕒 Last Login: {last_login}")
                else:
                    print(f"   🕒 Last Login: Never")
                print("-" * 50)
            
            print(f"\n📊 Total Users: {len(users)}")
            print("="*80)
            
        except Exception as e:
            print(f"❌ Error listing users: {e}")
        finally:
            if conn:
                conn.close()
    
    def change_password(self, username, new_password):
        """Change user password"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Hash the new password
            password_hash = self.hash_password(new_password)
            
            cursor.execute("""
                UPDATE users SET password_hash = %s WHERE username = %s
            """, (password_hash, username))
            
            if cursor.rowcount > 0:
                conn.commit()
                print(f"✅ Password changed successfully for user '{username}'")
                return True
            else:
                print(f"❌ User '{username}' not found")
                return False
                
        except Exception as e:
            print(f"❌ Error changing password: {e}")
            conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    def deactivate_user(self, username):
        """Deactivate a user"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users SET is_active = false WHERE username = %s
            """, (username,))
            
            if cursor.rowcount > 0:
                conn.commit()
                print(f"✅ User '{username}' deactivated successfully")
                return True
            else:
                print(f"❌ User '{username}' not found")
                return False
                
        except Exception as e:
            print(f"❌ Error deactivating user: {e}")
            conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    def activate_user(self, username):
        """Activate a user"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE users SET is_active = true WHERE username = %s
            """, (username,))
            
            if cursor.rowcount > 0:
                conn.commit()
                print(f"✅ User '{username}' activated successfully")
                return True
            else:
                print(f"❌ User '{username}' not found")
                return False
                
        except Exception as e:
            print(f"❌ Error activating user: {e}")
            conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

def main():
    """Main function to demonstrate user management"""
    user_manager = UserManager()
    
    print("🚀 Legal System User Management")
    print("="*50)
    
    # List current users
    user_manager.list_users()
    
    print("\n💡 Available Commands:")
    print("1. user_manager.list_users() - List all users")
    print("2. user_manager.create_user(username, email, password, full_name, role) - Create user")
    print("3. user_manager.change_password(username, new_password) - Change password")
    print("4. user_manager.deactivate_user(username) - Deactivate user")
    print("5. user_manager.activate_user(username) - Activate user")
    
    print("\n🔐 Current User Credentials:")
    import os
    admin_password = os.getenv('ADMIN_DEFAULT_PASSWORD', 'admin123')
    shantharam_password = os.getenv('SHANTHARAM_PASSWORD', 'shantharam123')
    rajaram_password = os.getenv('RAJARAM_PASSWORD', 'rajaram123')
    
    print(f"👑 Admin: username='admin', password='{admin_password}'")
    print(f"👤 Shantharam: username='shantharam', password='{shantharam_password}'")
    print(f"👤 Rajaram: username='rajaram', password='{rajaram_password}'")
    print("\n⚠️  WARNING: These are default passwords. Change them immediately!")

if __name__ == "__main__":
    main()


