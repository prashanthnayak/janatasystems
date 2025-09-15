# 🚀 Legal Management System - EC2 Deployment Guide

## 📋 Prerequisites
- Ubuntu 20.04+ EC2 instance
- At least 2GB RAM, 20GB storage
- Security groups allowing ports: 22 (SSH), 5002 (API), 8000 (Web)

## 🔧 Installation Steps

### Step 1: Upload Files to EC2
```bash
# From your local machine, upload files to EC2
scp -i your-key.pem install_ec2.sh ubuntu@YOUR_EC2_IP:~/
scp -i your-key.pem -r * ubuntu@YOUR_EC2_IP:~/legal_management/
```

### Step 2: Run Installation Script
```bash
# SSH into your EC2 instance
ssh -i your-key.pem ubuntu@YOUR_EC2_IP

# Make installation script executable and run it
chmod +x install_ec2.sh
./install_ec2.sh
```

### Step 3: Start the System
```bash
cd legal_management
./start_server.sh
```

## 🎯 Quick Commands

### Service Management
```bash
# Start service
sudo systemctl start legal-api

# Stop service
sudo systemctl stop legal-api

# Restart service
sudo systemctl restart legal-api

# Check status
sudo systemctl status legal-api

# View logs
journalctl -u legal-api -f
```

### Database Operations
```bash
# Connect to database
psql -U prashanth -d legal_management

# Run database setup
python database_setup.py

# Run migrations
python migrate_database.py
```

### Monitoring
```bash
# System status
./monitor.sh

# API health check
curl http://localhost:5002/api/health

# Check running processes
ps aux | grep python
```

## 🌐 Access URLs

- **API Server**: `http://YOUR_EC2_IP:5002`
- **Admin Dashboard**: `http://YOUR_EC2_IP:8000/admin_dashboard.html`
- **Login Page**: `http://YOUR_EC2_IP:8000/login.html`

## 🔐 Default Credentials

### Database
- **Username**: prashanth
- **Password**: secure_password_123
- **Database**: legal_management

### Admin User
- **Username**: admin
- **Password**: admin123

## 🔄 Deployment Workflow

### For Code Updates:
1. Upload new files to `~/upload/` on EC2
2. Run: `./deploy.sh`
3. Service will restart automatically

### Manual Deployment:
```bash
# Stop service
sudo systemctl stop legal-api

# Update code
cp -r ~/new_files/* .

# Run migrations if needed
python migrate_database.py

# Start service
sudo systemctl start legal-api
```

## 🛠️ Troubleshooting

### Common Issues:

#### Service Won't Start
```bash
# Check logs
journalctl -u legal-api -n 50

# Check if port is in use
sudo netstat -tulpn | grep 5002

# Check database connection
python -c "from database_setup import DatabaseManager; db = DatabaseManager(); print('✅ OK' if db.get_connection() else '❌ Failed')"
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Restart PostgreSQL
sudo systemctl restart postgresql

# Check database exists
sudo -u postgres psql -l | grep legal_management
```

#### Permission Issues
```bash
# Fix file permissions
chmod +x *.sh
chown -R $USER:$USER legal_management/

# Fix virtual environment
source venv/bin/activate
```

### Performance Tuning
```bash
# Monitor system resources
htop

# Check disk space
df -h

# Monitor API performance
tail -f /var/log/syslog | grep legal-api
```

## 📊 Security Checklist

- [ ] Update EC2 security groups
- [ ] Change default database password
- [ ] Enable firewall (UFW)
- [ ] Setup SSL certificates (optional)
- [ ] Regular system updates
- [ ] Monitor logs for suspicious activity

## 🔄 Backup Strategy

### Database Backup
```bash
# Create backup
pg_dump -U prashanth legal_management > backup_$(date +%Y%m%d).sql

# Restore backup
psql -U prashanth legal_management < backup_20241215.sql
```

### File Backup
```bash
# Backup entire project
tar -czf legal_management_backup_$(date +%Y%m%d).tar.gz legal_management/
```

## 📞 Support

If you encounter issues:
1. Check the logs: `journalctl -u legal-api -f`
2. Run monitoring script: `./monitor.sh`
3. Verify all services are running
4. Check EC2 security groups and firewall settings

---

**🎉 Your Legal Management System is now ready for production!**
