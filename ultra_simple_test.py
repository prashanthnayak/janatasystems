#!/usr/bin/env python3
"""
Ultra simple test with CORS support
"""

from flask import Flask, request, jsonify

app = Flask(__name__)

# Simple CORS handler
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/', methods=['GET'])
def home():
    return "Simple test server is working!"

@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json() or {}
    username = data.get('username', '')
    password = data.get('password', '')
    
    print(f"🔍 Login attempt - Username: {username}, Password: {password}")
    
    if username == 'admin' and password == 'admin123':
        return jsonify({
            'success': True, 
            'message': 'Login successful',
            'token': 'test_token_123',
            'user': {
                'username': 'admin',
                'role': 'admin',
                'full_name': 'Test Admin'
            }
        })
    elif username == 'user' and password == 'user123':
        return jsonify({
            'success': True, 
            'message': 'Login successful',
            'token': 'test_token_456',
            'user': {
                'username': 'user',
                'role': 'user',
                'full_name': 'Test User'
            }
        })
    else:
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5002, debug=False)
