#!/bin/bash
# Quick script to get token using curl

echo "🔍 Getting authentication token using curl..."

# Login and get token
curl -X POST http://localhost:5002/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "shantharam", "password": "password123"}' \
  | python3 -m json.tool

echo ""
echo "📋 Copy the 'token' value from the response above"
