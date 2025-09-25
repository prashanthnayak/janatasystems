#!/bin/bash
echo "🔍 Checking and restarting backend..."

# Check if backend is running
echo "📊 Checking if backend is running..."
if pgrep -f "python.*legal_api.py" > /dev/null; then
    echo "✅ Backend process found, stopping it..."
    pkill -f "python.*legal_api.py"
    sleep 2
else
    echo "❌ No backend process found"
fi

# Check if port 5002 is in use
echo "📊 Checking port 5002..."
if lsof -i :5002 > /dev/null 2>&1; then
    echo "⚠️ Port 5002 is still in use, killing processes..."
    lsof -ti :5002 | xargs kill -9
    sleep 2
fi

# Start the backend
echo "🚀 Starting backend..."
nohup python3 legal_api.py > backend.log 2>&1 &

# Wait a moment for startup
sleep 3

# Check if it's running
echo "📊 Checking if backend started successfully..."
if pgrep -f "python.*legal_api.py" > /dev/null; then
    echo "✅ Backend is running!"
    
    # Test if it's responding
    echo "📊 Testing backend response..."
    if curl -s http://localhost:5002/api/server-info > /dev/null; then
        echo "✅ Backend is responding to requests!"
    else
        echo "⚠️ Backend is running but not responding"
    fi
else
    echo "❌ Failed to start backend"
    echo "📋 Check backend.log for errors:"
    tail -10 backend.log
fi

echo "🔍 Backend status check complete"
