# VPS Deployment Guide for BFI Signals

## Server Setup Commands

### 1. Initial VPS Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y git python3 python3-pip python3-venv nginx certbot python3-certbot-nginx supervisor sqlite3

# Install Node.js (if needed for any frontend build processes)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 2. Setup User and Directory

```bash
# Create application user
sudo useradd -m -s /bin/bash bfi-signals
sudo usermod -aG sudo bfi-signals

# Switch to application user
sudo su - bfi-signals

# Create application directory
mkdir -p /home/bfi-signals/app
cd /home/bfi-signals/app
```

### 3. Clone and Setup Project

```bash
# Clone your repository
git clone https://github.com/YOUR_USERNAME/bfi-signals.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install additional production dependencies
pip install gunicorn

# Create environment file
cp .env.example .env
# Edit .env with your production settings
nano .env
```

### 4. Environment Configuration (.env)

```bash
# Production Environment Variables
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your_super_secret_key_here
DATABASE_URL=sqlite:///app.db

# Discord Integration
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL

# Trading Configuration
TRADING_SYMBOLS=^NDX
USE_ENHANCED_DISCORD=true

# Web server settings
HOST=0.0.0.0
PORT=5000
```

### 5. Setup Gunicorn Configuration

Create `/home/bfi-signals/app/gunicorn.conf.py`:

```python
bind = "127.0.0.1:5000"
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 60
keepalive = 2
preload_app = True
```

### 6. Create Systemd Service

Create `/etc/systemd/system/bfi-signals.service`:

```ini
[Unit]
Description=BFI Signals Flask Application
After=network.target

[Service]
User=bfi-signals
Group=bfi-signals
WorkingDirectory=/home/bfi-signals/app
Environment=PATH=/home/bfi-signals/app/venv/bin
ExecStart=/home/bfi-signals/app/venv/bin/gunicorn --config gunicorn.conf.py core.dashboard:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### 7. Configure Nginx

Create `/etc/nginx/sites-available/bonangfinance`:

```nginx
server {
    listen 80;
    server_name bonangfinance.co.za www.bonangfinance.co.za;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Handle static files
        location /static/ {
            alias /home/bfi-signals/app/core/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/bonangfinance /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 8. SSL Certificate Setup

```bash
# Get SSL certificate from Let's Encrypt
sudo certbot --nginx -d bonangfinance.co.za -d www.bonangfinance.co.za

# Test auto-renewal
sudo certbot renew --dry-run
```

### 9. Start Services

```bash
# Enable and start the application service
sudo systemctl daemon-reload
sudo systemctl enable bfi-signals.service
sudo systemctl start bfi-signals.service

# Check status
sudo systemctl status bfi-signals.service

# Enable and restart nginx
sudo systemctl enable nginx
sudo systemctl restart nginx
```

### 10. Database Setup

```bash
# Initialize database (if needed)
cd /home/bfi-signals/app
source venv/bin/activate
python -c "
import sqlite3
# Add any database initialization code here
"
```

## GitHub Actions Auto-Deployment Setup

### 1. Create GitHub Actions Workflow

Create `.github/workflows/deploy.yml` in your repository:

```yaml
name: Deploy to VPS

on:
  push:
    branches: [ main, master ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Deploy to server
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.VPS_HOST }}
        username: ${{ secrets.VPS_USER }}
        key: ${{ secrets.VPS_SSH_KEY }}
        script: |
          cd /home/bfi-signals/app
          git pull origin master
          source venv/bin/activate
          pip install -r requirements.txt
          sudo systemctl restart bfi-signals.service
          sudo systemctl reload nginx
```

### 2. Setup GitHub Secrets

In your GitHub repository settings, add these secrets:
- `VPS_HOST`: Your VPS IP address
- `VPS_USER`: bfi-signals
- `VPS_SSH_KEY`: Private SSH key content

### 3. Setup SSH Key on VPS

```bash
# On your VPS, as bfi-signals user
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Add your public key to authorized_keys
echo "your_public_key_here" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

## Monitoring and Maintenance

### View Application Logs
```bash
sudo journalctl -u bfi-signals.service -f
```

### View Nginx Logs
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Restart Services
```bash
sudo systemctl restart bfi-signals.service
sudo systemctl reload nginx
```

### Update Application
```bash
cd /home/bfi-signals/app
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart bfi-signals.service
```

## Security Considerations

### Firewall Setup
```bash
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
```

### Regular Updates
```bash
# Set up automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### Backup Script
Create `/home/bfi-signals/backup.sh`:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/bfi-signals/backups"
mkdir -p $BACKUP_DIR

# Backup database
cp /home/bfi-signals/app/core/ai_learning.db $BACKUP_DIR/ai_learning_$DATE.db

# Backup uploaded files (if any)
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz /home/bfi-signals/app/uploads/ 2>/dev/null || true

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

Make it executable and add to crontab:
```bash
chmod +x /home/bfi-signals/backup.sh
crontab -e
# Add this line for daily backups at 2 AM:
0 2 * * * /home/bfi-signals/backup.sh
```

## Troubleshooting

### Check Service Status
```bash
sudo systemctl status bfi-signals.service
sudo systemctl status nginx
```

### Check Ports
```bash
sudo netstat -tlnp | grep :5000
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443
```

### Test Application
```bash
curl -I http://localhost:5000
curl -I https://bonangfinance.co.za
```

Your BFI Signals application should now be deployed and accessible at https://bonangfinance.co.za with automatic updates from GitHub!