#!/usr/bin/env python3
"""
Simple Test API for Legal Management Software
Basic authentication without scraping functionality
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps

# Import database
from database_setup import DatabaseManager

app = Flask(__name__)
CORS(app)

# Initialize database
db = DatabaseManager()

# Authentication decorator
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        token = auth_header.split(' ')[1]
        user = db.get_user_by_session(token)
        
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
        user = db.get_user_by_session(token)
        
        if not user:
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401
        
        if user['role'] != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        request.current_user = user
        return f(*args, **kwargs)
    return decorated_function

# Authentication endpoints
@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password required'}), 400
        
        # Authenticate user
        user = db.authenticate_user(username, password)
        if not user:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
        # Generate session token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=24)
        
        # Create session
        if db.create_user_session(user['id'], token, expires_at):
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
        return jsonify({'success': False, 'error': 'Login failed'}), 500

@app.route('/api/auth/logout', methods=['POST'])
@require_auth
def logout():
    """User logout endpoint"""
    try:
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(' ')[1]
        
        # Remove session
        db.remove_user_session(token)
        
        return jsonify({'success': True, 'message': 'Logout successful'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'Logout failed'}), 500

@app.route('/api/auth/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get current user profile"""
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
        return jsonify({'success': False, 'error': 'Failed to get profile'}), 500

@app.route('/api/admin/users', methods=['GET'])
@require_admin
def get_users():
    """Get all users (admin only)"""
    try:
        users = db.get_all_users()
        return jsonify({'success': True, 'users': users})
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'Failed to get users'}), 500

@app.route('/api/cases', methods=['GET'])
def get_cases():
    """Get all cases from database"""
    try:
        cases = db.get_all_cases()
        return jsonify({'success': True, 'cases': cases})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/case_history/<cnr_number>', methods=['GET'])
def get_case_history(cnr_number):
    """Get case history for a specific case"""
    try:
        history = db.get_case_history(cnr_number)
        if history is not None:
            return jsonify({'success': True, 'history': history})
        else:
            return jsonify({'success': False, 'error': 'No case history found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("🚀 Starting Test API Server on port 5002...")
    app.run(host='0.0.0.0', port=5002, debug=True)
