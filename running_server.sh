# 1. 🔧 EC2 Security Groups (AWS Console or CLI)
# Allow these ports in your EC2 Security Group:
# - Port 22 (SSH) - already should be open
# - Port 80 (HTTP) - for web access
# - Port 5002 (API) - for direct API access
# - Port 8000 (HTTP Server) - for frontend

# 2. 🚀 Start both servers on EC2
# Terminal 1 - API Server
python3 legal_api.py &

# Terminal 2 - HTTP Server  
python3 -m http.server 8000 --bind 0.0.0.0 &

# 3. 🌐 Access your application
# Frontend: http://YOUR_EC2_PUBLIC_IP:8000
# API: http://YOUR_EC2_PUBLIC_IP:5002/api/...
