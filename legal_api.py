#!/usr/bin/env python3
"""
API for Legal Management Software
Handles CNR input from users and database operations
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import time
from datetime import datetime, timedelta
import threading
import queue
import sys
import hashlib
import secrets
from functools import wraps

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_setup import DatabaseManager
from scrapper import scrape_case_details

app = Flask(__name__)
#CORS(app)
# Dynamic CORS configuration
def get_cors_origins():
    """Get CORS origins dynamically"""
    try:
        import requests
        # Get current public IP
        response = requests.get('https://api.ipify.org', timeout=5)
        public_ip = response.text.strip()
        return [
            f"http://{public_ip}:8000",
            "http://localhost:8000",
            "http://127.0.0.1:8000"
        ]
    except:
        return ["http://localhost:8000", "http://127.0.0.1:8000"]

CORS(app,
     origins=get_cors_origins(),
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     supports_credentials=True)  # This is crucial!

# Global temporary storage for scraped data
temp_scraped_data = {}

# Global log storage (in-memory for real-time access)
system_logs = []
log_lock = threading.Lock()

class LegalAPI:
    def __init__(self):
        self.db = DatabaseManager()
    
    def add_log(self, message, log_type='info', source='system'):
        """Add a log entry to the system"""
        with log_lock:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entry = {
                'timestamp': timestamp,
                'message': message,
                'type': log_type,
                'source': source
            }
            system_logs.append(log_entry)
            
            # Keep only last 1000 logs to prevent memory issues
            if len(system_logs) > 1000:
                system_logs.pop(0)
    
    def get_logs(self, limit=100):
        """Get recent logs"""
        with log_lock:
            return system_logs[-limit:] if system_logs else []
    
    def clear_logs(self):
        """Clear all logs"""
        with log_lock:
            system_logs.clear()
    
    def convert_date_format(self, date_string):
        """Convert date from DD-MM-YYYY to YYYY-MM-DD format"""
        if not date_string or date_string == 'Unknown' or date_string == 'N/A':
            return None
        
        try:
            # Handle DD-MM-YYYY format (e.g., "19-12-2024")
            if '-' in date_string and len(date_string.split('-')) == 3:
                parts = date_string.split('-')
                if len(parts[0]) == 2 and len(parts[1]) == 2 and len(parts[2]) == 4:
                    # Convert DD-MM-YYYY to YYYY-MM-DD
                    return f"{parts[2]}-{parts[1]}-{parts[0]}"
        except:
            pass
        
        return date_string

    def add_case_with_cnr(self, cnr_number, case_data):
        """Add a case to the database with CNR number"""
        try:
            self.add_log(f"Adding case to database: {cnr_number}", 'info', 'database')
            
            # Extract case details
            case_title = case_data.get('case_title', 'N/A')
            client_name = case_data.get('client_name', 'N/A')
            client_phone = case_data.get('client_phone', '')
            client_email = case_data.get('client_email', '')
            petitioner = case_data.get('petitioner', 'N/A')
            respondent = case_data.get('respondent', 'N/A')
            case_type = case_data.get('case_type', 'N/A')
            court_name = case_data.get('court_name', 'N/A')
            judge_name = case_data.get('judge_name', 'N/A')
            status = case_data.get('status', 'Active')
            filing_date = self.convert_date_format(case_data.get('filing_date'))
            case_description = case_data.get('case_description', '')
            registration_number = case_data.get('registration_number')
            user_id = case_data.get('user_id')  # Get user_id from case_data
            
            # Insert case into database
            success = self.db.insert_case(
                cnr_number,
                case_title=case_title,
                client_name=client_name,
                client_phone=client_phone,
                client_email=client_email,
                petitioner=petitioner,
                respondent=respondent,
                case_type=case_type,
                court_name=court_name,
                judge_name=judge_name,
                status=status,
                filing_date=filing_date,
                case_description=case_description,
                registration_number=registration_number,
                user_id=user_id  # Pass user_id to database
            )
            
            if not success:
                self.add_log(f"Failed to insert case: {cnr_number}", 'error', 'database')
                return {'success': False, 'error': 'Failed to insert case into database'}
            
            # Insert case history if available
            case_history = case_data.get('case_history', [])
            history_success_count = 0
            
            for row in case_history:
                success = self.db.insert_case_history(
                    cnr_number,
                    row.get("Judge", ""),
                    self.convert_date_format(row.get("Business_on_Date", "")),
                    self.convert_date_format(row.get("Hearing_Date", "")),
                    row.get("Purpose_of_Hearing", ""),
                    row.get("Status", ""),  # Add status parameter (optional)
                    user_id=user_id  # Pass user_id for case history
                )
                if success:
                    history_success_count += 1
            
            self.add_log(f"Case added successfully: {cnr_number} with {history_success_count} history records", 'success', 'database')
                
            return {
                'success': True,
                'message': f'Case added successfully with {history_success_count} history records',
                'case_history_count': history_success_count
            }
        except Exception as e:
            self.add_log(f"Database error: {str(e)}", 'error', 'database')
            return {'success': False, 'error': str(e)}
    
    def trigger_scraping(self, cnr_number):
        """Step 1: Trigger scraping and store in temporary storage with retry logic"""
        MAX_RETRIES = 3
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                self.add_log(f"Starting scraping attempt {attempt} of {MAX_RETRIES} for CNR: {cnr_number}", 'info', 'scraper')
                
                # Scrape the data
                result = scrape_case_details(cnr_number)
                
                if result and result.get('success'):
                    # Step 2: Store in temporary storage
                    temp_scraped_data[cnr_number] = result
                    self.add_log(f"Scraping completed successfully on attempt {attempt} for CNR: {cnr_number}", 'success', 'scraper')
                    
                    return {
                        'success': True,
                        'message': f'Scraping completed successfully on attempt {attempt}',
                        'data': result,
                        'extracted_real_data': result.get('extracted_real_data', False)
                    }
                else:
                    error_msg = result.get('error', 'Unknown scraping error') if result else 'No result from scraper'
                    self.add_log(f"Scraping failed on attempt {attempt} for CNR {cnr_number}: {error_msg}", 'error', 'scraper')
                    
                    if attempt < MAX_RETRIES:
                        self.add_log(f"Retrying in 5 seconds... (attempt {attempt + 1} of {MAX_RETRIES})", 'info', 'scraper')
                        time.sleep(5)
                    else:
                        return {
                            'success': False,
                            'error': f"All {MAX_RETRIES} attempts failed. Last error: {error_msg}"
                        }
                        
            except Exception as e:
                self.add_log(f"Error on attempt {attempt}: {str(e)}", 'error', 'scraper')
                
                if attempt < MAX_RETRIES:
                    self.add_log(f"Retrying in 5 seconds... (attempt {attempt + 1} of {MAX_RETRIES})", 'info', 'scraper')
                    time.sleep(5)
                else:
                    return {'success': False, 'error': f"All {MAX_RETRIES} attempts failed. Last error: {str(e)}"}
        
        return {'success': False, 'error': 'All retry attempts failed'}
    
    def save_to_database(self, cnr_number, user_data):
        """Save case data directly from form to database"""
        try:
            self.add_log(f"Saving case to database: {cnr_number}", 'info', 'database')
            
            # Get scraped data from temporary storage (optional)
            scraped_data = temp_scraped_data.get(cnr_number, {})
            
            # Create case data directly from form (user data takes priority)
            combined_data = {
                'cnr_number': cnr_number,
                'case_title': user_data.get('case_title', 'N/A'),
                'client_name': user_data.get('client_name', 'N/A'),
                'client_phone': user_data.get('client_phone', ''),
                'client_email': user_data.get('client_email', ''),
                'petitioner': user_data.get('petitioner') or scraped_data.get('petitioner', 'N/A'),
                'respondent': user_data.get('respondent') or scraped_data.get('respondent', 'N/A'),
                'case_type': user_data.get('case_type') or scraped_data.get('case_type', 'N/A'),
                'court_name': user_data.get('court_name') or scraped_data.get('court_name', 'N/A'),
                'judge_name': user_data.get('judge_name') or scraped_data.get('judge_name', 'N/A'),
                'filing_date': user_data.get('filing_date') or self.convert_date_format(scraped_data.get('filing_date')),
                'case_description': user_data.get('case_description', ''),
                'registration_number': user_data.get('registration_number') or scraped_data.get('registration_number', 'N/A'),
                'user_id': user_data.get('user_id'),  # Include user_id from authenticated user
                'case_history': scraped_data.get('case_history', [])
            }
            
            # Save to database
            result = self.add_case_with_cnr(cnr_number, combined_data)
            
            if result.get('success'):
                # Clear temporary data after successful save
                if cnr_number in temp_scraped_data:
                    del temp_scraped_data[cnr_number]
                self.add_log(f"Data saved to database and temporary storage cleared for CNR: {cnr_number}", 'success', 'database')
            
            return result
                
        except Exception as e:
            self.add_log(f"Error saving to database: {str(e)}", 'error', 'database')
            return {'success': False, 'error': str(e)}
    
    def get_scraped_data(self, cnr_number):
        """Get scraped data from temporary storage"""
        return temp_scraped_data.get(cnr_number, None)

# Initialize API
legal_api = LegalAPI()

# User cache to avoid repeated database queries
user_cache = {}

def get_cached_user(token):
    """Get user from cache if available and not expired"""
    if token in user_cache:
        user_data, expiry_time = user_cache[token]
        if time.time() < expiry_time:
            print(f"✅ CACHE: User found in cache for token: {token[:10]}...")
            return user_data
        else:
            # Token expired, remove from cache
            print(f"⏰ CACHE: Token expired, removing from cache: {token[:10]}...")
            del user_cache[token]
    else:
        print(f"❌ CACHE: No user found in cache for token: {token[:10]}...")
    return None

def cache_user(token, user_data, expiry_hours=24):
    """Cache user data with expiry time"""
    expiry_time = time.time() + (expiry_hours * 3600)
    user_cache[token] = (user_data, expiry_time)
    print(f"💾 CACHE: User cached for token: {token[:10]}... (expires in {expiry_hours}h)")

def clear_user_cache(token=None):
    """Clear user cache - either specific token or all"""
    if token:
        user_cache.pop(token, None)
        print(f"🗑️ CACHE: Cleared cache for specific token: {token[:10]}...")
    else:
        user_cache.clear()
        print("🗑️ CACHE: Cleared all user cache")

# Authentication decorator
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from request headers
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Authorization header required'}), 401
        
        token = auth_header.split(' ')[1]
        
        # Try to get user from cache first
        user = get_cached_user(token)

        # If not in cache, query database and cache the result
        if not user:
            user = legal_api.db.get_user_by_session(token)
            if user:
                cache_user(token, user)
                print(f"🔍 DEBUG: User cached for token: {token[:10]}...")
            else:
                return jsonify({'success': False, 'error': 'Invalid session'}), 401
        else:
            print(f"🚀 CACHE HIT: User loaded from cache for token: {token[:10]}...")

        # Add user to request context for use in route functions
        request.user = user
        return f(*args, **kwargs)
    
    return decorated_function

# Admin-only decorator
def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First check authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        token = auth_header.split(' ')[1]
        user = legal_api.db.get_user_by_session(token)
        
        if not user:
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401
        
        # Then check if user is admin
        if user['role'] != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        request.current_user = user
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Get system logs"""
    try:
        limit = request.args.get('limit', 100, type=int)
        logs = legal_api.get_logs(limit)
        return jsonify({'success': True, 'logs': logs})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/logs/clear', methods=['POST'])
def clear_logs():
    """Clear all logs"""
    try:
        legal_api.clear_logs()
        return jsonify({'success': True, 'message': 'Logs cleared'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/logs/add', methods=['POST'])
def add_log():
    """Add a log entry"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        log_type = data.get('type', 'info')
        source = data.get('source', 'system')
        
        legal_api.add_log(message, log_type, source)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/scraping/trigger/<cnr_number>', methods=['POST'])
def trigger_scraping(cnr_number):
    """Step 1: Trigger scraping"""
    return jsonify(legal_api.trigger_scraping(cnr_number))

@app.route('/api/cases/save', methods=['POST'])
@require_auth
def save_case():
    """Step 3: Save case to database"""
    try:
        # Get user from token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Authorization header required'}), 401
        
        token = auth_header.split(' ')[1]
        user = legal_api.db.get_user_by_session(token)
        
        if not user:
            return jsonify({'success': False, 'error': 'Invalid session'}), 401
        
        data = request.get_json()
        cnr_number = data.get('cnr_number')
        user_data = data.get('user_data', {})
        
        if not cnr_number:
            return jsonify({'success': False, 'error': 'CNR number is required'})
        
        # Add user_id to user_data so it gets saved with the case
        user_data['user_id'] = user['id']
        
        return jsonify(legal_api.save_to_database(cnr_number, user_data))

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/scraping/data/<cnr_number>', methods=['GET'])
def get_scraped_data(cnr_number):
    """Get scraped data from temporary storage"""
    data = legal_api.get_scraped_data(cnr_number)
    if data:
        return jsonify({'success': True, 'data': data})
    else:
        return jsonify({'success': False, 'error': 'No scraped data found'})

@app.route('/api/cases', methods=['GET'])
def get_cases():
    """Get cases from database - admin sees all, users see only their own"""
    try:
        # Get user from token
        auth_header = request.headers.get('Authorization')
        print(f"🔍 DEBUG: Auth header: {auth_header}")
        
        if not auth_header or not auth_header.startswith('Bearer '):
            print("🔍 DEBUG: No auth header or invalid format")
            return jsonify({'success': False, 'error': 'Authorization header required'}), 401
        
        token = auth_header.split(' ')[1]
        print(f"🔍 DEBUG: Token: {token}")
        
        user = legal_api.db.get_user_by_session(token)
        print(f"🔍 DEBUG: User from session: {user}")
        
        if not user:
            print("🔍 DEBUG: No user found for token")
            return jsonify({'success': False, 'error': 'Invalid session'}), 401
        
        # Admin users see all cases, regular users see only their own
        if user['role'] == 'admin':
            cases = legal_api.db.get_all_cases()
        else:
            cases = legal_api.db.get_cases_for_user(user['id'])
        
        return jsonify({'success': True, 'cases': cases})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/cases/<cnr_number>', methods=['GET', 'PUT', 'DELETE', 'OPTIONS'])
def handle_case(cnr_number):
    """Handle GET, PUT, and DELETE operations for a specific case"""
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        return '', 200
    
    # Get user from cached authentication (already validated by require_auth if needed)
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'success': False, 'error': 'Authorization header required'}), 401
    
    token = auth_header.split(' ')[1]
    
    # Try to get user from cache first
    user = get_cached_user(token)
    
    # If not in cache, query database and cache the result
    if not user:
        user = legal_api.db.get_user_by_session(token)
        if user:
            cache_user(token, user)
        else:
            return jsonify({'success': False, 'error': 'Invalid session'}), 401
        
    if request.method == 'GET':
        """Get specific case by CNR"""
        try:
            case = legal_api.db.get_case(cnr_number)
            if case:
                # Check if user can access this case (admin or owner)
                if user['role'] != 'admin' and case.get('user_id') != user['id']:
                    return jsonify({'success': False, 'error': 'Access denied'}), 403
                
                return jsonify({'success': True, 'case': case})
            else:
                return jsonify({'success': False, 'error': 'Case not found'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    elif request.method == 'PUT':
        """Update specific case by CNR"""
        try:
            # Check if user can modify this case (admin or owner)
            case = legal_api.db.get_case(cnr_number)
            if not case:
                return jsonify({'success': False, 'error': 'Case not found'}), 404

            if user['role'] != 'admin' and case.get('user_id') != user['id']:
                return jsonify({'success': False, 'error': 'Access denied'}), 403

            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': 'No data provided for update'}), 400

            # Map frontend field names to database column names
            mapped_data = {}
            field_mapping = {
                'caseTitle': 'case_title',
                'clientName': 'client_name',
                'caseNumber': 'registration_number',
                'caseType': 'case_type',
                'court': 'court_name',
                'filingDate': 'filing_date',
                'caseDescription': 'case_description',
                'user_id': 'user_id'  # Allow updating user_id
            }

            for frontend_key, db_key in field_mapping.items():
                if frontend_key in data and data[frontend_key]:
                    mapped_data[db_key] = data[frontend_key]

            # Update the case with mapped data
            success = legal_api.db.update_case(cnr_number, mapped_data)
            if success:
                legal_api.add_log(f"Case updated successfully: {cnr_number}", 'info', 'database')
                return jsonify({'success': True, 'message': f'Case {cnr_number} updated successfully'})
            else:
                return jsonify({'success': False, 'error': 'Failed to update case'}), 500
        except Exception as e:
            legal_api.add_log(f"Error updating case {cnr_number}: {str(e)}", 'error', 'database')
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'DELETE':
        """Delete specific case by CNR"""
        try:
            # Check if user can delete this case (admin or owner)
            case = legal_api.db.get_case(cnr_number)
            if not case:
                return jsonify({'success': False, 'error': 'Case not found'}), 404
            
            if user['role'] != 'admin' and case.get('user_id') != user['id']:
                return jsonify({'success': False, 'error': 'Access denied'}), 403
            
            success = legal_api.db.delete_case(cnr_number)
            if success:
                legal_api.add_log(f"Case deleted successfully: {cnr_number}", 'info', 'database')
                return jsonify({'success': True, 'message': f'Case {cnr_number} deleted successfully'})
            else:
                return jsonify({'success': False, 'error': 'Failed to delete case'})
        except Exception as e:
            legal_api.add_log(f"Error deleting case {cnr_number}: {str(e)}", 'error', 'database')
            return jsonify({'success': False, 'error': str(e)})

@app.route('/api/cases/histories/batch', methods=['GET'])
@require_auth
def get_batch_case_history():
    """Get case history for all user's cases in one API call (FAST!)"""
    try:
        # Get user from token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Authorization header required'}), 401
        
        token = auth_header.split(' ')[1]
        user = legal_api.db.get_user_by_session(token)
        
        if not user:
            return jsonify({'success': False, 'error': 'Invalid session'}), 401
        
        # Get all cases for the user
        if user['role'] == 'admin':
            cases = legal_api.db.get_all_cases()
        else:
            cases = legal_api.db.get_cases_for_user(user['id'])
        
        if not cases:
            return jsonify({'success': True, 'all_histories': {}})
        
        # Get case history for all cases in one batch
        all_histories = {}
        for case in cases:
            cnr_number = case['cnr_number']
            history = legal_api.db.get_case_history(cnr_number)
            if history:
                all_histories[cnr_number] = {
                    'case_title': case.get('case_title', 'Unknown'),
                    'case_type': case.get('case_type', 'Unknown'),
                    'history': history
                }
        
        legal_api.add_log(f"Retrieved batch case history for {len(cases)} cases", 'success', 'database')
        return jsonify({
            'success': True, 
            'all_histories': all_histories,
            'total_cases': len(cases),
            'total_histories': len(all_histories)
        })
        
    except Exception as e:
        legal_api.add_log(f"Error getting batch case history: {str(e)}", 'error', 'database')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/user/dashboard-data', methods=['GET', 'OPTIONS'])
def get_user_dashboard_data():
    """Get ALL user data in ONE API call - SUPER FAST! 🚀"""
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        return '', 200
    
    # Apply authentication only for non-OPTIONS requests
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'success': False, 'error': 'Authorization header required'}), 401
    
    token = auth_header.split(' ')[1]
    user = get_cached_user(token)
    
    # If not in cache, query database and cache the result
    if not user:
        user = legal_api.db.get_user_by_session(token)
        if user:
            cache_user(token, user)
    
    if not user:
        return jsonify({'success': False, 'error': 'Invalid session'}), 401
    
    try:
        
        # Get all cases for the user
        if user['role'] == 'admin':
            cases = legal_api.db.get_all_cases()
        else:
            cases = legal_api.db.get_cases_for_user(user['id'])
        
        # Get case history for all cases in one batch
        all_histories = {}
        calendar_events = []
        
        for case in cases:
            cnr_number = case['cnr_number']
            history = legal_api.db.get_case_history(cnr_number)
            if history:
                all_histories[cnr_number] = {
                    'case_title': case.get('case_title', 'Unknown'),
                    'case_type': case.get('case_type', 'Unknown'),
                    'history': history
                }
                
                # Create calendar events from history
                for entry in history:
                    if entry.get('hearing_date'):
                        event_title = f"{case.get('case_title', 'Unknown Case')} - {entry.get('purpose', 'Hearing')}"
                        print(f"🔍 DEBUG: Creating calendar event for {cnr_number}:")
                        print(f"   case_title: '{case.get('case_title', 'Unknown Case')}'")
                        print(f"   case_type: '{case.get('case_type', 'Unknown')}'")
                        print(f"   purpose: '{entry.get('purpose', 'Hearing')}'")
                        print(f"   final_title: '{event_title}'")
                        
                        calendar_events.append({
                            'date': entry['hearing_date'].isoformat() if hasattr(entry['hearing_date'], 'isoformat') else str(entry['hearing_date']),
                            'title': event_title,
                            'description': entry.get('order_details', 'No details available'),
                            'caseTitle': case.get('case_title', 'Unknown Case'),
                            'cnrNumber': cnr_number,
                            'type': 'hearing',
                            'time': '09:00 AM'  # Default time
                        })
        
        # Extract unique clients from cases
        clients = []
        clients_map = {}
        
        for case in cases:
            # Add client_name as primary client
            if case.get('client_name') and case['client_name'].strip() and case['client_name'] != 'Unknown':
                client_name = case['client_name']
                if client_name not in clients_map:
                    clients_map[client_name] = {
                        'name': client_name,
                        'type': 'Individual',
                        'email': '',
                        'phone': '',
                        'location': case.get('court_name', 'Unknown Court'),
                        'status': 'Active',
                        'activeCases': 0,
                        'totalBilled': 'N/A',
                        'role': 'Primary Client',
                        'cnr': case['cnr_number'],
                        'caseType': case['case_type']
                    }
                clients_map[client_name]['activeCases'] += 1
            
            # Add petitioner as client
            if case.get('petitioner') and case['petitioner'].strip() and case['petitioner'] != 'Unknown':
                client_name = case['petitioner']
                if client_name not in clients_map:
                    clients_map[client_name] = {
                        'name': client_name,
                        'type': 'Individual',
                        'email': '',
                        'phone': '',
                        'location': case.get('court_name', 'Unknown Court'),
                        'status': 'Active',
                        'activeCases': 0,
                        'totalBilled': 'N/A',
                        'role': 'Petitioner',
                        'cnr': case['cnr_number'],
                        'caseType': case['case_type']
                    }
                clients_map[client_name]['activeCases'] += 1
        
        clients = list(clients_map.values())
        
        legal_api.add_log(f"Retrieved complete dashboard data for user {user['username']}: {len(cases)} cases, {len(clients)} clients, {len(calendar_events)} events", 'success', 'database')
        
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'full_name': user['full_name'],
                'role': user['role']
            },
            'dashboard_data': {
                'cases': cases,
                'case_histories': all_histories,
                'clients': clients,
                'calendar_events': calendar_events,
                'summary': {
                    'total_cases': len(cases),
                    'total_clients': len(clients),
                    'total_events': len(calendar_events),
                    'active_cases': len([c for c in cases if c.get('status') == 'Active'])
                }
            },
            'cache_version': int(time.time() * 1000)  # Add timestamp for cache versioning
        })
        
    except Exception as e:
        legal_api.add_log(f"Error getting user dashboard data: {str(e)}", 'error', 'database')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/case_history/<cnr_number>', methods=['GET'])
@require_auth
def get_case_history(cnr_number):
    """Get case history for a specific case"""
    try:
        # Get user from token for authorization check
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Authorization header required'}), 401
        
        token = auth_header.split(' ')[1]
        user = legal_api.db.get_user_by_session(token)
        
        if not user:
            return jsonify({'success': False, 'error': 'Invalid session'}), 401
        
        # Check if user can access this case (admin or owner)
        case = legal_api.db.get_case(cnr_number)
        if not case:
            return jsonify({'success': False, 'error': 'Case not found'}), 404
        
        if user['role'] != 'admin' and case.get('user_id') != user['id']:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        history = legal_api.db.get_case_history(cnr_number)
        if history is not None:
            legal_api.add_log(f"Retrieved {len(history)} history records for CNR: {cnr_number}", 'success', 'database')
            return jsonify({'success': True, 'history': history})
        else:
            legal_api.add_log(f"No case history found for CNR: {cnr_number}", 'info', 'database')
            return jsonify({'success': False, 'error': 'No case history found'})
    except Exception as e:
        legal_api.add_log(f"Error getting case history for CNR {cnr_number}: {str(e)}", 'error', 'database')
        return jsonify({'success': False, 'error': str(e)})

# Authentication endpoints
@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    """User login endpoint"""
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password required'}), 400
        
        # Authenticate user
        user_data = legal_api.db.authenticate_user(username, password)
        if not user_data:
            legal_api.add_log(f"Failed login attempt for username: {username}", 'warning', 'auth')
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
        # Create user session
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=24)
        
        if legal_api.db.create_user_session(user_data['id'], session_token, expires_at):
            # Clear any old cached data for this user
            clear_user_cache()
            
            # Cache the new user session
            cache_user(session_token, user_data)
            
            legal_api.add_log(f"User {user_data['username']} logged in successfully", 'success', 'auth')
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'token': session_token,
                'user': {
                    'id': user_data['id'],
                    'username': user_data['username'],
                    'email': user_data['email'],
                    'full_name': user_data['full_name'],
                    'role': user_data['role']
                }
            })
        else:
            legal_api.add_log(f"Failed to create session for user {user_data['username']}", 'error', 'auth')
            return jsonify({'success': False, 'error': 'Failed to create session'}), 500
            
    except Exception as e:
        legal_api.add_log(f"Login error: {str(e)}", 'error', 'auth')
        return jsonify({'success': False, 'error': 'Login failed'}), 500

@app.route('/api/auth/logout', methods=['POST', 'OPTIONS'])
@require_auth
def logout():
    """Logout user and invalidate session"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Authorization header required'}), 401
        
        token = auth_header.split(' ')[1]
        
        # Remove session from database
        legal_api.db.remove_user_session(token)
        
        # Clear user from cache
        clear_user_cache(token)
        
        legal_api.add_log(f"User {request.user['username']} logged out", 'info', 'auth')
        return jsonify({'success': True, 'message': 'Logout successful'})
        
    except Exception as e:
        legal_api.add_log(f"Error during logout: {str(e)}", 'error', 'auth')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/profile', methods=['GET', 'OPTIONS'])
@require_auth
def get_profile():
    """Get current user profile"""
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        return jsonify({
            'success': True,
            'user': {
                'id': request.user['id'],
                'username': request.user['username'],
                'email': request.user['email'],
                'full_name': request.user['full_name'],
                'role': request.user['role']
            }
        })
    except Exception as e:
        legal_api.add_log(f"Profile error: {str(e)}", 'error', 'auth')
        return jsonify({'success': False, 'error': 'Failed to get profile'}), 500

@app.route('/api/admin/users', methods=['GET'])
@require_admin
def get_users():
    """Get all users (admin only)"""
    try:
        users = legal_api.db.get_all_users()
        
        legal_api.add_log(f"Admin {request.current_user['username']} retrieved user list", 'info', 'admin')
        return jsonify({'success': True, 'users': users})
        
    except Exception as e:
        legal_api.add_log(f"Get users error: {str(e)}", 'error', 'admin')
        return jsonify({'success': False, 'error': 'Failed to get users'}), 500

@app.route('/api/admin/users/create', methods=['POST', 'OPTIONS'])
def create_user():
    """Create new user (admin only)"""
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        return '', 200
    
    # For POST requests, check admin authentication
    if request.method == 'POST':
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        token = auth_header.split(' ')[1]
        user = legal_api.db.get_user_by_session(token)
        
        if not user:
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401
        
        # Check if user is admin
        if user['role'] != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        request.current_user = user
        
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'fullName', 'email', 'password', 'role']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                'success': False, 
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Extract user data
        username = data.get('username').strip()
        full_name = data.get('fullName').strip()
        email = data.get('email').strip()
        phone = data.get('phone', '').strip()
        password = data.get('password')
        role = data.get('role')
        status = data.get('status', 'active')
        
        # Validate email format
        import re
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_pattern, email):
            return jsonify({'success': False, 'error': 'Invalid email format'}), 400
        
        # Validate role
        if role not in ['admin', 'user']:
            return jsonify({'success': False, 'error': 'Role must be either "admin" or "user"'}), 400
        
        # Validate status
        if status not in ['active', 'inactive']:
            return jsonify({'success': False, 'error': 'Status must be either "active" or "inactive"'}), 400
        
        # Check if username already exists
        try:
            existing_user = legal_api.db.get_user_by_username(username)
            if existing_user:
                return jsonify({'success': False, 'error': 'Username already exists'}), 400
        except Exception as e:
            print(f"Error checking existing user: {e}")
            pass  # Continue if method fails
        
        # Hash password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Create user using the database manager
        user_id = legal_api.db.create_user(
            username=username,
            password_hash=password_hash,
            email=email,
            full_name=full_name,
            phone=phone,
            role=role,
            status=status
        )
        
        if user_id:
            legal_api.add_log(
                f"Admin {request.current_user['username']} created new user: {username} ({role})", 
                'success', 'admin'
            )
            return jsonify({
                'success': True, 
                'message': f'User "{username}" created successfully',
                'user_id': user_id
            })
        else:
            legal_api.add_log(f"Failed to create user: {username}", 'error', 'admin')
            return jsonify({'success': False, 'error': 'Failed to create user - database operation failed'}), 500
            
    except Exception as e:
        legal_api.add_log(f"Error creating user: {str(e)}", 'error', 'admin')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>', methods=['PUT', 'OPTIONS'])
def update_user(user_id):
    """Update existing user (admin only)"""
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        return '', 200
    
    # For PUT requests, check admin authentication
    if request.method == 'PUT':
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        token = auth_header.split(' ')[1]
        user = legal_api.db.get_user_by_session(token)
        
        if not user:
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401
        
        # Check if user is admin
        if user['role'] != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        request.current_user = user
        
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['username', 'fullName', 'email', 'role']
            missing_fields = [field for field in required_fields if not data.get(field)]
            
            if missing_fields:
                return jsonify({
                    'success': False, 
                    'error': f'Missing required fields: {", ".join(missing_fields)}'
                }), 400
            
            # Extract user data
            username = data.get('username').strip()
            full_name = data.get('fullName').strip()
            email = data.get('email').strip()
            phone = data.get('phone', '').strip()
            role = data.get('role')
            status = data.get('status', 'active')
            
            # Validate email format
            import re
            email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
            if not re.match(email_pattern, email):
                return jsonify({'success': False, 'error': 'Invalid email format'}), 400
            
            # Validate role
            if role not in ['admin', 'user']:
                return jsonify({'success': False, 'error': 'Role must be either "admin" or "user"'}), 400
            
            # Validate status
            if status not in ['active', 'inactive']:
                return jsonify({'success': False, 'error': 'Status must be either "active" or "inactive"'}), 400
            
            # Check if username already exists for different user
            try:
                existing_user = legal_api.db.get_user_by_username(username)
                if existing_user and existing_user['id'] != user_id:
                    return jsonify({'success': False, 'error': 'Username already exists'}), 400
            except:
                pass
            
            # Update user
            success = legal_api.db.update_user(
                user_id=user_id,
                username=username,
                email=email,
                full_name=full_name,
                phone=phone,
                role=role,
                status=status
            )
            
            if success:
                legal_api.add_log(
                    f"Admin {request.current_user['username']} updated user: {username} ({role})", 
                    'success', 'admin'
                )
                return jsonify({
                    'success': True, 
                    'message': f'User "{username}" updated successfully'
                })
            else:
                return jsonify({'success': False, 'error': 'Failed to update user'}), 500
                
        except Exception as e:
            legal_api.add_log(f"Error updating user: {str(e)}", 'error', 'admin')
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE', 'OPTIONS'])
def delete_user(user_id):
    """Delete user (admin only)"""
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        return '', 200
    
    # For DELETE requests, check admin authentication
    if request.method == 'DELETE':
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        token = auth_header.split(' ')[1]
        user = legal_api.db.get_user_by_session(token)
        
        if not user:
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401
        
        # Check if user is admin
        if user['role'] != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        # Prevent admin from deleting themselves
        if user['id'] == user_id:
            return jsonify({'success': False, 'error': 'Cannot delete your own account'}), 400
        
        request.current_user = user
        
        try:
            # Get user details for logging
            user_to_delete = legal_api.db.get_user_by_id(user_id)
            if not user_to_delete:
                return jsonify({'success': False, 'error': 'User not found'}), 404
            
            # Delete user
            success = legal_api.db.delete_user(user_id)
            
            if success:
                username = user_to_delete["username"]
                legal_api.add_log(
                    f"Admin {request.current_user['username']} deleted user: {username}", 
                    'success', 'admin'
                )
                return jsonify({
                    'success': True, 
                    'message': f'User "{username}" deleted successfully'
                })
            else:
                return jsonify({'success': False, 'error': 'Failed to delete user'}), 500
                
        except Exception as e:
            legal_api.add_log(f"Error deleting user: {str(e)}", 'error', 'admin')
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/server-info', methods=['GET'])
def get_server_info():
    """Get server information including public IP"""
    try:
        import requests
        
        # Get public IP from multiple sources
        public_ip = None
        ip_services = [
            'https://api.ipify.org',
            'https://checkip.amazonaws.com',
            'https://ipinfo.io/ip'
        ]
        
        for service in ip_services:
            try:
                response = requests.get(service, timeout=5)
                if response.status_code == 200:
                    public_ip = response.text.strip()
                    break
            except:
                continue
        
        # Get local IP as fallback
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        return jsonify({
            'success': True,
            'public_ip': public_ip,
            'local_ip': local_ip,
            'hostname': hostname,
            'api_port': 5002,
            'web_port': 8000
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'local_ip': '127.0.0.1',
            'api_port': 5002,
            'web_port': 8000
        })

if __name__ == '__main__':
    legal_api.add_log("API server starting up", 'info', 'system')
    print("🚀 Starting Legal API Server on port 5002...")
    app.run(host='0.0.0.0', port=5002, debug=False) 
