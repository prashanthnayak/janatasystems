#!/usr/bin/env python3
"""
Database setup for Legal Management System
Creates PostgreSQL tables for cases, case history, and scraping logs
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        # Database connection parameters
        self.db_params = {
            'host': 'localhost',  # Changed from 52.23.206.51 to localhost
            'database': 'legal_management',
            'user': 'prashanth',
            'password': 'secure_password_123',
            'port': '5432'
        }
    
    def get_connection(self):
        """Get database connection"""
        try:
            conn = psycopg2.connect(**self.db_params)
            return conn
        except Exception as e:
            print(f"Database connection error: {e}")
            return None
    
    def create_tables(self):
        """Create all necessary tables"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Create cases table with CNR as primary key
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cases (
                    cnr_number VARCHAR(16) PRIMARY KEY,
                    case_title VARCHAR(255),
                    client_name VARCHAR(255),
                    petitioner VARCHAR(255),
                    respondent VARCHAR(255),
                    case_type VARCHAR(50),
                    court_name VARCHAR(255),
                    judge_name VARCHAR(255),
                    status VARCHAR(50),
                    filing_date DATE,
                    case_description TEXT,
                    registration_number VARCHAR(50),
                    user_id INTEGER REFERENCES users(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create case_history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS case_history (
                    id SERIAL PRIMARY KEY,
                    cnr_number VARCHAR(16) NOT NULL,
                    judge VARCHAR(100),
                    business_date DATE,
                    hearing_date DATE,
                    purpose TEXT,
                    order_details TEXT,
                    next_hearing_date DATE,
                    user_id INTEGER REFERENCES users(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (cnr_number) REFERENCES cases(cnr_number)
                )
            """)
            
            # Create scraping_logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scraping_logs (
                    id SERIAL PRIMARY KEY,
                    cnr_number VARCHAR(16) UNIQUE NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    records_scraped INTEGER DEFAULT 0,
                    error_message TEXT,
                    execution_time FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create users table for multi-user authentication
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    full_name VARCHAR(100) NOT NULL,
                    phone VARCHAR(15),
                    role VARCHAR(10) DEFAULT 'user',
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            """)
            
            # Create user_sessions table for session management
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    session_token VARCHAR(255) UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            print("✅ Database tables created successfully")
            
            # Create default admin user and migrate existing data
            self.create_default_admin()
            self.add_user_id_to_existing_tables()
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def create_users_table(self):
        """Create users table for multi-user authentication"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    full_name VARCHAR(100) NOT NULL,
                    role VARCHAR(10) DEFAULT 'user',
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT NOW(),
                    last_login TIMESTAMP
                )
            """)
            
            # Create user_sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    session_token VARCHAR(255) UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            conn.commit()
            print("✅ Users table created successfully")
            
            # Create default admin user if not exists
            self.create_default_admin()
            
        except Exception as e:
            print(f"❌ Error creating users table: {e}")
            conn.rollback()
        finally:
            if conn:
                conn.close()

    def create_default_admin(self):
        """Create default admin user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if admin user exists
            cursor.execute("SELECT id FROM users WHERE username = 'admin'")
            if cursor.fetchone() is None:
                # Hash the default password
                import hashlib
                password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
                
                # Create default admin user
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, full_name, role)
                    VALUES (%s, %s, %s, %s, %s)
                """, ('admin', 'admin@legalsystem.com', password_hash, 'System Administrator', 'admin'))
                
                conn.commit()
                print("✅ Default admin user created (username: admin, password: admin123)")
            else:
                print("ℹ️ Admin user already exists")
                
        except Exception as e:
            print(f"❌ Error creating admin user: {e}")
            conn.rollback()
        finally:
            if conn:
                conn.close()

    def add_user_id_to_existing_tables(self):
        """Add user_id column to existing tables and migrate data"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Add user_id to cases table if not exists
            cursor.execute("""
                ALTER TABLE cases 
                ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id)
            """)
            
            # Add user_id to case_history table if not exists
            cursor.execute("""
                ALTER TABLE case_history 
                ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id)
            """)
            
            # Get admin user ID
            cursor.execute("SELECT id FROM users WHERE username = 'admin'")
            admin_id = cursor.fetchone()
            
            if admin_id:
                # Migrate existing data to admin user
                cursor.execute("UPDATE cases SET user_id = %s WHERE user_id IS NULL", (admin_id[0],))
                cursor.execute("UPDATE case_history SET user_id = %s WHERE user_id IS NULL", (admin_id[0],))
                print("✅ Existing data migrated to admin user")
            
            conn.commit()
            print("✅ User ID columns added to existing tables")
            
        except Exception as e:
            print(f"❌ Error adding user_id columns: {e}")
            conn.rollback()
        finally:
            if conn:
                conn.close()

    def insert_case(self, cnr_number, case_title, client_name=None, petitioner=None, respondent=None, case_type=None, court_name=None, judge_name=None, status=None, filing_date=None, case_description=None, registration_number=None, user_id=None):
        """Insert or update case in database"""
        conn = self.get_connection()
        if not conn:
            print(f"❌ Database: Failed to get connection for CNR: {cnr_number}")
            return False
        
        try:
            cursor = conn.cursor()
            
            # Use UPSERT (INSERT ... ON CONFLICT) to handle duplicate CNR
            cursor.execute("""
                INSERT INTO cases (cnr_number, case_title, client_name, petitioner, respondent, case_type, court_name, judge_name, status, filing_date, case_description, registration_number, user_id, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (cnr_number) 
                DO UPDATE SET 
                    case_title = EXCLUDED.case_title,
                    client_name = EXCLUDED.client_name,
                    petitioner = EXCLUDED.petitioner,
                    respondent = EXCLUDED.respondent,
                    case_type = EXCLUDED.case_type,
                    court_name = EXCLUDED.court_name,
                    judge_name = EXCLUDED.judge_name,
                    status = EXCLUDED.status,
                    filing_date = EXCLUDED.filing_date,
                    case_description = EXCLUDED.case_description,
                    registration_number = EXCLUDED.registration_number,
                    user_id = EXCLUDED.user_id,
                    updated_at = CURRENT_TIMESTAMP
            """, (cnr_number, case_title, client_name, petitioner, respondent, case_type, court_name, judge_name, status, filing_date, case_description, registration_number, user_id))
            
            conn.commit()
            print(f"✅ Database: Case inserted/updated successfully for CNR: {cnr_number}")
            return True
            
        except Exception as e:
            print(f"❌ Database: Error inserting/updating case for CNR {cnr_number}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
            print(f"🗄️ Database: Connection closed for CNR: {cnr_number}")

    def insert_case_history_simple(self, cnr_number, hearing_date, purpose):
        """Insert case history entry with current table structure - prevents duplicates"""
        conn = self.get_connection()
        if not conn:
            print(f"❌ Database: Failed to get connection for case history CNR: {cnr_number}")
            return False
        
        try:
            cursor = conn.cursor()
            
            # Convert date string to proper format if needed
            try:
                if hearing_date and hearing_date != '':
                    hearing_date = datetime.strptime(hearing_date, '%d-%m-%Y').date()
                else:
                    hearing_date = None
            except:
                hearing_date = None
            
            # Check if this exact entry already exists to prevent duplicates
            cursor.execute("""
                SELECT COUNT(*) FROM case_history 
                WHERE cnr_number = %s AND hearing_date = %s AND purpose = %s
            """, (cnr_number, hearing_date, purpose))
            
            existing_count = cursor.fetchone()[0]
            
            if existing_count > 0:
                print(f"⚠️ Database: Case history entry already exists for CNR: {cnr_number}, Date: {hearing_date}")
                return "existing"  # Return "existing" to indicate it was already there
            
            # Insert only if it doesn't exist
            cursor.execute("""
                INSERT INTO case_history (cnr_number, hearing_date, purpose)
                VALUES (%s, %s, %s)
            """, (cnr_number, hearing_date, purpose))
            
            conn.commit()
            print(f"✅ Database: New case history entry inserted for CNR: {cnr_number}")
            return "new"  # Return "new" to indicate it was inserted
            
        except Exception as e:
            print(f"❌ Database: Error inserting case history for CNR {cnr_number}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
            print(f"🗄️ Database: Connection closed for case history CNR: {cnr_number}")

    def clean_duplicate_case_history(self):
        """Remove duplicate case history entries, keeping only one copy of each unique entry"""
        conn = self.get_connection()
        if not conn:
            print("❌ Database: Failed to get connection for cleaning duplicates")
            return False
        
        try:
            cursor = conn.cursor()
            
            # First, count total duplicates
            cursor.execute("""
                SELECT COUNT(*) FROM (
                    SELECT cnr_number, hearing_date, purpose, COUNT(*) as count
                    FROM case_history 
                    GROUP BY cnr_number, hearing_date, purpose
                    HAVING COUNT(*) > 1
                ) as duplicates
            """)
            duplicate_sets = cursor.fetchone()[0]
            
            if duplicate_sets == 0:
                print("✅ Database: No duplicate case history entries found")
                return True
            
            print(f"🧹 Database: Found {duplicate_sets} sets of duplicate case history entries")
            
            # Delete duplicates, keeping only the entry with the smallest ID for each unique combination
            cursor.execute("""
                DELETE FROM case_history 
                WHERE id NOT IN (
                    SELECT MIN(id) 
                    FROM case_history 
                    GROUP BY cnr_number, hearing_date, purpose
                )
            """)
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            print(f"✅ Database: Successfully removed {deleted_count} duplicate case history entries")
            print(f"📊 Database: Kept {duplicate_sets} unique case history entries")
            
            return True
            
        except Exception as e:
            print(f"❌ Database: Error cleaning duplicate case history: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
            print("🗄️ Database: Connection closed after cleaning duplicates")

    def insert_case_history(self, cnr_number, judge, business_date, hearing_date, purpose, status=None, user_id=None):
        """Insert case history entry into database"""
        conn = self.get_connection()
        if not conn:
            print(f"❌ Database: Failed to get connection for case history CNR: {cnr_number}")
            return False
        
        try:
            cursor = conn.cursor()
            
            print(f"🔍 Database: Raw dates - Business: '{business_date}', Hearing: '{hearing_date}'")
            
            # Convert date strings to proper format if needed
            if business_date and business_date != '' and business_date != 'None':
                try:
                    if '-' in business_date:
                        if business_date.count('-') == 2:
                            # Check if it's YYYY-MM-DD or DD-MM-YYYY
                            parts = business_date.split('-')
                            if len(parts[0]) == 4:  # YYYY-MM-DD format
                                business_date = datetime.strptime(business_date, '%Y-%m-%d').date()
                            else:  # DD-MM-YYYY format
                                business_date = datetime.strptime(business_date, '%d-%m-%Y').date()
                        else:
                            business_date = None
                    else:
                        business_date = None
                except:
                    business_date = None
            else:
                business_date = None
                
            if hearing_date and hearing_date != '' and hearing_date != 'None':
                try:
                    if '-' in hearing_date:
                        if hearing_date.count('-') == 2:
                            # Check if it's YYYY-MM-DD or DD-MM-YYYY
                            parts = hearing_date.split('-')
                            if len(parts[0]) == 4:  # YYYY-MM-DD format
                                hearing_date = datetime.strptime(hearing_date, '%Y-%m-%d').date()
                            else:  # DD-MM-YYYY format
                                hearing_date = datetime.strptime(hearing_date, '%d-%m-%Y').date()
                        else:
                            hearing_date = None
                    else:
                        hearing_date = None
                except:
                    hearing_date = None
            else:
                hearing_date = None
            
            cursor.execute("""
                INSERT INTO case_history (cnr_number, judge, business_date, hearing_date, purpose, order_details, status, user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (cnr_number, judge, business_date, hearing_date, purpose, None, status, user_id))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Database: Error inserting case history for CNR {cnr_number}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_case(self, cnr_number):
        """Get case by CNR number"""
        print(f"🗄️ Database: Attempting to get case with CNR: {cnr_number}")
        conn = self.get_connection()
        if not conn:
            print(f"❌ Database: Failed to get connection for CNR: {cnr_number}")
            return None
        
        try:
            cursor = conn.cursor()
            print(f"🗄️ Database: Executing SELECT query for CNR: {cnr_number}")
            cursor.execute("""
                SELECT cnr_number, case_title, petitioner, respondent, case_type, court_name, judge_name, status, filing_date, case_description, registration_number, created_at, updated_at, client_name, user_id
                FROM cases 
                WHERE cnr_number = %s
            """, (cnr_number,))
            
            row = cursor.fetchone()
            if row:
                case_data = {
                    'cnr_number': row[0],
                    'case_title': row[1],
                    'petitioner': row[2],
                    'respondent': row[3],
                    'case_type': row[4],
                    'court_name': row[5],
                    'judge_name': row[6],
                    'status': row[7],
                    'filing_date': row[8],
                    'case_description': row[9],
                    'registration_number': row[10],
                    'created_at': row[11],
                    'updated_at': row[12],
                    'client_name': row[13],
                    'user_id': row[14]
                }
                print(f"✅ Database: Case found for CNR {cnr_number}: {case_data}")
                return case_data
            else:
                print(f"❌ Database: No case found for CNR: {cnr_number}")
                return None
                
        except Exception as e:
            print(f"❌ Database: Error getting case for CNR {cnr_number}: {e}")
            return None
        finally:
            conn.close()
            print(f"🗄️ Database: Connection closed for CNR: {cnr_number}")
    
    def get_all_cases(self):
        """Get all cases from database"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT cnr_number, case_title, petitioner, respondent, case_type, court_name, judge_name, status, filing_date, case_description, registration_number, created_at, updated_at, client_name, user_id
                FROM cases 
                ORDER BY created_at DESC
            """)
            
            rows = cursor.fetchall()
            cases = []
            for row in rows:
                case_data = {
                    'cnr_number': row[0],
                    'case_title': row[1],
                    'petitioner': row[2],
                    'respondent': row[3],
                    'case_type': row[4],
                    'court_name': row[5],
                    'judge_name': row[6],
                    'status': row[7],
                    'filing_date': row[8],
                    'case_description': row[9],
                    'registration_number': row[10],
                    'created_at': row[11],
                    'updated_at': row[12],
                    'client_name': row[13],
                    'user_id': row[14]
                }
                cases.append(case_data)
            
            return cases
                
        except Exception as e:
            print(f"❌ Database: Error getting all cases: {e}")
            return []
        finally:
            conn.close()

    def get_cases_for_user(self, user_id):
        """Get all cases for a specific user"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT cnr_number, case_title, petitioner, respondent, case_type, court_name, judge_name, status, filing_date, case_description, registration_number, created_at, updated_at, client_name, user_id
                FROM cases 
                WHERE user_id = %s
                ORDER BY created_at DESC
            """, (user_id,))
            
            rows = cursor.fetchall()
            cases = []
            for row in rows:
                case_data = {
                    'cnr_number': row[0],
                    'case_title': row[1],
                    'petitioner': row[2],
                    'respondent': row[3],
                    'case_type': row[4],
                    'court_name': row[5],
                    'judge_name': row[6],
                    'status': row[7],
                    'filing_date': row[8],
                    'case_description': row[9],
                    'registration_number': row[10],
                    'created_at': row[11],
                    'updated_at': row[12],
                    'client_name': row[13],
                    'user_id': row[14]
                }
                cases.append(case_data)
            
            return cases
                
        except Exception as e:
            print(f"❌ Database: Error getting cases for user {user_id}: {e}")
            return []
        finally:
            conn.close()
    
    def update_scraping_status(self, cnr_number, status, records_scraped=0, error_message=None, execution_time=None):
        """Update scraping status"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO scraping_logs (cnr_number, status, records_scraped, error_message, execution_time)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (cnr_number) DO UPDATE SET
                    status = EXCLUDED.status,
                    records_scraped = EXCLUDED.records_scraped,
                    error_message = EXCLUDED.error_message,
                    execution_time = EXCLUDED.execution_time,
                    updated_at = CURRENT_TIMESTAMP
            """, (cnr_number, status, records_scraped, error_message, execution_time))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Error updating scraping status: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_scraping_status(self, cnr_number):
        """Get scraping status for a CNR"""
        conn = self.get_connection()
        if not conn:
            return {'status': 'ERROR', 'error_message': 'Database connection failed'}
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM scraping_logs 
                WHERE cnr_number = %s 
                ORDER BY updated_at DESC 
                LIMIT 1
            """, (cnr_number,))
            
            status = cursor.fetchone()
            if status:
                return dict(status)
            else:
                return {'status': 'NOT_FOUND'}
            
        except Exception as e:
            print(f"❌ Error getting scraping status: {e}")
            return {'status': 'ERROR', 'error_message': str(e)}
        finally:
            conn.close()
    
    def update_case(self, cnr_number, case_data):
        """Update case in database"""
        print(f"🗄️ Database: Attempting to update case with CNR: {cnr_number}")
        print(f"🗄️ Database: Update data: {case_data}")
        conn = self.get_connection()
        if not conn:
            print(f"❌ Database: Failed to get connection for CNR: {cnr_number}")
            return False
        
        try:
            cursor = conn.cursor()
            print(f"🗄️ Database: Executing UPDATE query for CNR: {cnr_number}")
            
            # Build dynamic UPDATE query
            set_clauses = []
            values = []
            
            for key, value in case_data.items():
                if key != 'cnr_number' and key != 'created_at' and key != 'updated_at':
                    set_clauses.append(f"{key} = %s")
                    values.append(value)
            
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            
            query = f"""
                UPDATE cases 
                SET {', '.join(set_clauses)}
                WHERE cnr_number = %s
            """
            
            # Add cnr_number for WHERE clause
            values.append(cnr_number)
            
            cursor.execute(query, values)
            rows_affected = cursor.rowcount
            print(f"🗄️ Database: UPDATE query executed, rows affected: {rows_affected}")
            
            conn.commit()
            print(f"✅ Database: Case updated successfully for CNR: {cnr_number}")
            return True
            
        except Exception as e:
            print(f"❌ Database: Error updating case for CNR {cnr_number}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
            print(f"🗄️ Database: Connection closed for CNR: {cnr_number}")

    def migrate_add_client_name(self):
        """Add client_name column to existing cases table"""
        conn = self.get_connection()
        if not conn:
            print("❌ Database: Failed to get connection for migration")
            return False
        
        try:
            cursor = conn.cursor()
            
            # Check if client_name column already exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'cases' AND column_name = 'client_name'
            """)
            
            if cursor.fetchone():
                print("✅ Database: client_name column already exists")
                return True
            
            # Add client_name column
            cursor.execute("""
                ALTER TABLE cases 
                ADD COLUMN client_name VARCHAR(255)
            """)
            
            conn.commit()
            print("✅ Database: Successfully added client_name column to cases table")
            return True
            
        except Exception as e:
            print(f"❌ Database: Error adding client_name column: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def delete_case_history(self, cnr_number):
        """Delete all case history entries for a given CNR"""
        print(f"🗄️ Database: Attempting to delete case history for CNR: {cnr_number}")
        conn = self.get_connection()
        if not conn:
            print(f"❌ Database: Failed to get connection for deleting history CNR: {cnr_number}")
            return 0
        
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM case_history WHERE cnr_number = %s", (cnr_number,))
            rows_deleted = cursor.rowcount
            conn.commit()
            print(f"✅ Database: Deleted {rows_deleted} case history entries for CNR: {cnr_number}")
            return rows_deleted
            
        except Exception as e:
            print(f"❌ Database: Error deleting case history for CNR {cnr_number}: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()
            print(f"🗄️ Database: Connection closed for deleting history CNR: {cnr_number}")
    
    def get_case_history(self, cnr_number):
        """Get case history for a specific case"""
        conn = self.get_connection()
        if not conn:
            print(f"❌ Database: Failed to get connection for CNR: {cnr_number}")
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT judge, business_date, hearing_date, purpose, created_at
                FROM case_history 
                WHERE cnr_number = %s 
                ORDER BY created_at DESC
            """, (cnr_number,))
            
            rows = cursor.fetchall()
            history = []
            
            for row in rows:
                history.append({
                    'judge': row[0] or 'N/A',
                    'business_date': row[1].strftime('%Y-%m-%d') if row[1] else 'N/A',
                    'hearing_date': row[2].strftime('%Y-%m-%d') if row[2] else 'N/A',
                    'purpose': row[3] or 'N/A',
                    'created_at': row[4].strftime('%Y-%m-%d %H:%M:%S') if row[4] else 'N/A'
                })
            
            print(f"✅ Database: Retrieved {len(history)} history records for CNR: {cnr_number}")
            return history
            
        except Exception as e:
            print(f"❌ Database: Failed to get case history for CNR {cnr_number}: {e}")
            return None
        finally:
            conn.close()
            print(f"🗄️ Database: Connection closed for CNR: {cnr_number}")
    
    def delete_case(self, cnr_number):
        """Delete case and all related data"""
        conn = self.get_connection()
        if not conn:
            print(f"❌ Database: Failed to get connection for CNR: {cnr_number}")
            return False
        
        try:
            cursor = conn.cursor()
            
            # Delete case history first (due to foreign key constraint)
            cursor.execute("DELETE FROM case_history WHERE cnr_number = %s", (cnr_number,))
            
            # Delete the case
            cursor.execute("DELETE FROM cases WHERE cnr_number = %s", (cnr_number,))
            
            conn.commit()
            print(f"✅ Database: Case and related data deleted for CNR: {cnr_number}")
            return True
                
        except Exception as e:
            print(f"❌ Database: Error deleting case for CNR {cnr_number}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
            print(f"🗄️ Database: Connection closed for CNR: {cnr_number}")

    def fix_case_history_table(self):
        """Add missing columns to case_history table if they don't exist"""
        conn = self.get_connection()
        if not conn:
            print("❌ Database: Failed to get connection for table fix")
            return False
        
        try:
            cursor = conn.cursor()
            
            # Check if judge column exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'case_history' AND column_name = 'judge'
            """)
            
            if not cursor.fetchone():
                print("🔧 Adding missing 'judge' column to case_history table...")
                cursor.execute("ALTER TABLE case_history ADD COLUMN judge VARCHAR(100)")
                print("✅ Added 'judge' column to case_history table")
            
            # Check if business_date column exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'case_history' AND column_name = 'business_date'
            """)
            
            if not cursor.fetchone():
                print("🔧 Adding missing 'business_date' column to case_history table...")
                cursor.execute("ALTER TABLE case_history ADD COLUMN business_date DATE")
                print("✅ Added 'business_date' column to case_history table")
            
            # Check if order_details column exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'case_history' AND column_name = 'order_details'
            """)
            
            if not cursor.fetchone():
                print("🔧 Adding missing 'order_details' column to case_history table...")
                cursor.execute("ALTER TABLE case_history ADD COLUMN order_details TEXT")
                print("✅ Added 'order_details' column to case_history table")
            
            # Check if next_hearing_date column exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'case_history' AND column_name = 'next_hearing_date'
            """)
            
            if not cursor.fetchone():
                print("🔧 Adding missing 'next_hearing_date' column to case_history table...")
                cursor.execute("ALTER TABLE case_history ADD COLUMN next_hearing_date DATE")
                print("✅ Added 'next_hearing_date' column to case_history table")
            
            # Check if status column exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'case_history' AND column_name = 'status'
            """)
            
            if not cursor.fetchone():
                print("🔧 Adding missing 'status' column to case_history table...")
                cursor.execute("ALTER TABLE case_history ADD COLUMN status TEXT")
                print("✅ Added 'status' column to case_history table")
            
            conn.commit()
            print("✅ Database: case_history table structure fixed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Database: Error fixing case_history table: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
            print("🗄️ Database: Connection closed after table fix")

    def authenticate_user(self, username, password):
        """Authenticate user with username and password"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Hash the password for comparison
            import hashlib
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            cursor.execute("""
                SELECT id, username, email, full_name, role, is_active
                FROM users 
                WHERE username = %s AND password_hash = %s AND is_active = true
            """, (username, password_hash))
            
            user = cursor.fetchone()
            if user:
                return {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'full_name': user[3],
                    'role': user[4]
                }
            return None
                
        except Exception as e:
            print(f"❌ Error authenticating user: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def create_user_session(self, user_id, session_token, expires_at):
        """Create a new user session"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO user_sessions (user_id, session_token, expires_at)
                VALUES (%s, %s, %s)
            """, (user_id, session_token, expires_at))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Error creating user session: {e}")
            conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def get_user_by_session(self, session_token):
        """Get user by session token"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT u.id, u.username, u.email, u.full_name, u.role
                FROM users u
                JOIN user_sessions s ON u.id = s.user_id
                WHERE s.session_token = %s AND s.expires_at > NOW() AND u.is_active = true
            """, (session_token,))
            
            user = cursor.fetchone()
            if user:
                return {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'full_name': user[3],
                    'role': user[4]
                }
            return None
            
        except Exception as e:
            print(f"❌ Error getting user by session: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def remove_user_session(self, session_token):
        """Remove a user session (logout)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM user_sessions WHERE session_token = %s
            """, (session_token,))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Error removing user session: {e}")
            conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def get_all_users(self):
        """Get all users (admin only)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, username, email, full_name, phone, role, is_active, created_at, last_login
                FROM users ORDER BY role, username
            """)
            
            rows = cursor.fetchall()
            users = []
            for row in rows:
                user_data = {
                    'id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'full_name': row[3],
                    'phone': row[4],
                    'role': row[5],
                    'is_active': row[6],
                    'created_at': row[7],
                    'last_login': row[8]
                }
                users.append(user_data)
            
            return users
                
        except Exception as e:
            print(f"❌ Error getting all users: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def create_user(self, username, password_hash, email, full_name, phone=None, role='user', status='active'):
        """Create a new user"""
        try:
            conn = self.get_connection()
            if not conn:
                return None
            
            cursor = conn.cursor()
            
            # Insert new user (using is_active instead of status for compatibility)
            is_active = status == 'active'
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, full_name, phone, role, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                RETURNING id
            """, (username, email, password_hash, full_name, phone, role, is_active))
            
            user_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            
            return user_id
            
        except Exception as e:
            print(f"Error creating user: {e}")
            return None

    def get_user_by_username(self, username):
        """Get user by username"""
        try:
            conn = self.get_connection()
            if not conn:
                return None
            
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, email, full_name, phone, role, is_active
                FROM users
                WHERE username = %s
            """, (username,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                columns = ['id', 'username', 'email', 'full_name', 'phone', 'role', 'is_active']
                return dict(zip(columns, result))
            
            return None
            
        except Exception as e:
            print(f"Error getting user by username: {e}")
            return None

    def get_user_by_email(self, email):
        """Get user by email"""
        try:
            conn = self.get_connection()
            if not conn:
                return None
            
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, email, full_name, phone, role, is_active
                FROM users
                WHERE email = %s
            """, (email,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                columns = ['id', 'username', 'email', 'full_name', 'phone', 'role', 'is_active']
                return dict(zip(columns, result))
            
            return None
            
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None

    def get_user_by_id(self, user_id):
        """Get user by ID"""
        try:
            conn = self.get_connection()
            if not conn:
                return None
            
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, email, full_name, phone, role, is_active
                FROM users
                WHERE id = %s
            """, (user_id,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                columns = ['id', 'username', 'email', 'full_name', 'phone', 'role', 'is_active']
                return dict(zip(columns, result))
            
            return None
            
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None

    def update_user(self, user_id, username, email, full_name, phone=None, role='user', status='active'):
        """Update existing user"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            # Update user
            is_active = status == 'active'
            cursor.execute("""
                UPDATE users 
                SET username = %s, email = %s, full_name = %s, phone = %s, role = %s, is_active = %s
                WHERE id = %s
            """, (username, email, full_name, phone, role, is_active, user_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                cursor.close()
                conn.close()
                return True
            else:
                cursor.close()
                conn.close()
                return False
                
        except Exception as e:
            print(f"Error updating user: {e}")
            return False

    def delete_user(self, user_id):
        """Delete user by ID"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            # Delete user
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            
            if cursor.rowcount > 0:
                conn.commit()
                cursor.close()
                conn.close()
                return True
            else:
                cursor.close()
                conn.close()
                return False
                
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False

    def add_phone_column_to_users(self):
        """Add phone column to users table if it doesn't exist"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
                
            cursor = conn.cursor()
            
            # Check if phone column exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='phone'
            """)
            
            if not cursor.fetchone():
                # Add phone column
                cursor.execute("ALTER TABLE users ADD COLUMN phone VARCHAR(15)")
                conn.commit()
                print("✅ Added phone column to users table")
            else:
                print("✅ Phone column already exists in users table")
            
            return True
            
        except Exception as e:
            print(f"❌ Error adding phone column: {e}")
            return False
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    def recreate_users_table(self):
        """Drop and recreate users table with correct structure"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Drop existing users table if it exists
            cursor.execute("DROP TABLE IF EXISTS user_sessions CASCADE")
            cursor.execute("DROP TABLE IF EXISTS users CASCADE")
            
            # Recreate users table with correct structure
            cursor.execute("""
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    full_name VARCHAR(100) NOT NULL,
                    phone VARCHAR(15),
                    role VARCHAR(10) DEFAULT 'user',
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            """)
            
            # Recreate user_sessions table
            cursor.execute("""
                CREATE TABLE user_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    session_token VARCHAR(255) UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            print("✅ Users table recreated with correct structure")
            
            # Create default admin user
            self.create_default_admin()
            
        except Exception as e:
            print(f"❌ Error recreating users table: {e}")
            conn.rollback()
        finally:
            if conn:
                conn.close()

# Initialize database
if __name__ == "__main__":
    db_manager = DatabaseManager()
    db_manager.create_tables()
    db_manager.migrate_add_client_name() 
    db_manager.add_phone_column_to_users()  # Recreate users table with correct structure 
