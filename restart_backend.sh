#!/bin/bash
echo "🔄 Restarting backend with CORS fix..."

# Kill any existing backend processes
echo "🛑 Stopping existing backend processes..."
sudo pkill -f "python.*legal_api.py" || echo "No existing processes found"

# Wait a moment
sleep 2

# Navigate to project directory (adjust path as needed)
cd /home/ec2-user/janatasystems 2>/dev/null || cd /home/ubuntu/janatasystems 2>/dev/null || cd . 2>/dev/null

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Start backend
echo "🚀 Starting backend..."
nohup python3 legal_api.py > backend.log 2>&1 &

# Wait for backend to start
sleep 3

# Check if backend is running
echo "🔍 Checking if backend started..."
if pgrep -f "python.*legal_api.py" > /dev/null; then
    echo "✅ Backend is running!"
    echo "📋 Process info:"
    ps aux | grep "python.*legal_api.py" | grep -v grep
else
    echo "❌ Backend failed to start. Check backend.log for errors:"
    tail -20 backend.log
fi

echo "🔍 Testing backend connectivity..."
python3 -c "
import requests
try:
    response = requests.get('http://localhost:5002/api/server-info', timeout=5)
    print(f'✅ Backend responding: {response.status_code}')
except Exception as e:
    print(f'❌ Backend not responding: {e}')
"