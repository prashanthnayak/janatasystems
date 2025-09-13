#!/usr/bin/env python3
"""
Working Legal API - Authentication only (no scrapper import)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
CORS(app)

# Simple CORS handler
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Temporary user storage (will be replaced with database later)
users_db = {
    'admin': {
        'id': 1,
        'username': 'admin',
        'password_hash': hashlib.sha256('admin123'.encode()).hexdigest(),
        'email': 'admin@legalsystem.com',
        'full_name': 'System Administrator',
        'role': 'admin'
    },
    'user': {
        'id': 2,
        'username': 'user',
        'password_hash': hashlib.sha256('user123'.encode()).hexdigest(),
        'email': 'user@legalsystem.com',
        'full_name': 'Regular User',
        'role': 'user'
    }
}

# Temporary session storage
sessions = {}

def authenticate_user(username, password):
    """Authenticate user with username and password"""
    user = users_db.get(username)
    if user:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if user['password_hash'] == password_hash:
            return user
    return None

def create_user_session(user_id, token, expires_at):
    """Create a new user session"""
    sessions[token] = {
        'user_id': user_id,
        'expires_at': expires_at
    }
    return True

def get_user_by_session(token):
    """Get user by session token"""
    session = sessions.get(token)
    if session and session['expires_at'] > datetime.now():
        # Find user by ID
        for user in users_db.values():
            if user['id'] == session['user_id']:
                return user
    return None

def remove_user_session(token):
    """Remove a user session (logout)"""
    if token in sessions:
        del sessions[token]
        return True
    return False

# Authentication decorator
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        token = auth_header.split(' ')[1]
        user = get_user_by_session(token)
        
        if not user:
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401
        
        request.current_user = user
        return f(*args, **kwargs)
    return decorated_function

# Admin-only decorator
def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        token = auth_header.split(' ')[1]
        user = get_user_by_session(token)
        
        if not user:
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401
        
        if user['role'] != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        request.current_user = user
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=['GET'])
def home():
    return jsonify({'status': 'Legal API server is running!', 'version': '2.0'})

@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    """User login endpoint"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json() or {}
        username = data.get('username', '')
        password = data.get('password', '')
        
        print(f"🔍 Login attempt - Username: {username}")
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password required'}), 400
        
        # Authenticate user
        user = authenticate_user(username, password)
        if not user:
            print(f"❌ Failed login attempt for username: {username}")
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
        # Generate session token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=24)
        
        # Create session
        if create_user_session(user['id'], token, expires_at):
            print(f"✅ User {username} logged in successfully")
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'token': token,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'full_name': user['full_name'],
                    'role': user['role']
                }
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to create session'}), 500
            
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return jsonify({'success': False, 'error': 'Login failed'}), 500

@app.route('/api/auth/logout', methods=['POST', 'OPTIONS'])
@require_auth
def logout():
    """User logout endpoint"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1]
        
        # Remove session
        remove_user_session(token)
        
        print(f"✅ User {request.current_user['username']} logged out")
        return jsonify({'success': True, 'message': 'Logout successful'})
        
    except Exception as e:
        print(f"❌ Logout error: {str(e)}")
        return jsonify({'success': False, 'error': 'Logout failed'}), 500

@app.route('/api/auth/profile', methods=['GET', 'OPTIONS'])
@require_auth
def get_profile():
    """Get current user profile"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        return jsonify({
            'success': True,
            'user': {
                'id': request.current_user['id'],
                'username': request.current_user['username'],
                'email': request.current_user['email'],
                'full_name': request.current_user['full_name'],
                'role': request.current_user['role']
            }
        })
    except Exception as e:
        print(f"❌ Profile error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to get profile'}), 500

@app.route('/api/admin/users', methods=['GET', 'OPTIONS'])
@require_admin
def get_users():
    """Get all users (admin only)"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        users_list = []
        for user in users_db.values():
            users_list.append({
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'full_name': user['full_name'],
                'role': user['role'],
                'is_active': True
            })
        
        print(f"✅ Admin {request.current_user['username']} retrieved user list")
        return jsonify({'success': True, 'users': users_list})
        
    except Exception as e:
        print(f"❌ Get users error: {str(e)}")
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
        user = get_user_by_session(token)
        
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
        
        # Check if username already exists
        if username in users_db:
            return jsonify({'success': False, 'error': 'Username already exists'}), 400
        
        # Hash password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Create new user ID
        new_user_id = max([user['id'] for user in users_db.values()]) + 1
        
        # Create user in memory
        users_db[username] = {
            'id': new_user_id,
            'username': username,
            'password_hash': password_hash,
            'email': email,
            'full_name': full_name,
            'phone': phone,
            'role': role,
            'is_active': status == 'active'
        }
        
        print(f"✅ Admin {request.current_user['username']} created new user: {username} ({role})")
        return jsonify({
            'success': True, 
            'message': f'User "{username}" created successfully',
            'user_id': new_user_id
        })
            
    except Exception as e:
        print(f"❌ Error creating user: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Working Legal API Server on port 5002...")
    app.run(host='0.0.0.0', port=5002, debug=False)


