#!/usr/bin/env python3
"""
Simple login test without database - just to test if login works
"""

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Simple login test - hardcoded admin/admin123"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        print(f"🔍 Login attempt - Username: {username}, Password: {password}")
        
        # Simple hardcoded check
        if username == 'admin' and password == 'admin123':
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'token': 'test_token_123',
                'user': {
                    'id': 1,
                    'username': 'admin',
                    'email': 'admin@test.com',
                    'full_name': 'Test Admin',
                    'role': 'admin'
                }
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return jsonify({'success': False, 'error': 'Login failed'}), 500

@app.route('/', methods=['GET'])
def home():
    """Basic test endpoint"""
    return jsonify({'status': 'Simple login test server is running!'})

if __name__ == '__main__':
    print("🚀 Starting Simple Login Test Server on port 5002...")
    app.run(host='0.0.0.0', port=5002, debug=True)


