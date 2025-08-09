# Quick Deploy Commands for bonangfinance.co.za

## Copy and paste these commands on your VPS:

### 1. System Setup (Run as root)
```bash
# Update system and install dependencies
apt update && apt upgrade -y
apt install -y git python3 python3-pip python3-venv nginx certbot python3-certbot-nginx supervisor sqlite3 curl

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
apt-get install -y nodejs

# Create application user
useradd -m -s /bin/bash bfi-signals
usermod -aG sudo bfi-signals
```

### 2. Setup Application (Run as bfi-signals user)
```bash
# Switch to app user and setup directory
sudo su - bfi-signals
mkdir -p /home/bfi-signals/app
cd /home/bfi-signals/app

# Clone repository (replace with your actual GitHub repo)
git clone https://github.com/YOUR_USERNAME/bfi-signals.git .

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# Create production environment file
cat > .env << 'EOF'
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your_super_secret_production_key_change_this
DATABASE_URL=sqlite:///ai_learning.db

# Discord Integration - ADD YOUR WEBHOOK URL
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL

# Trading Configuration
TRADING_SYMBOLS=^NDX
USE_ENHANCED_DISCORD=true

# Web server settings
HOST=0.0.0.0
PORT=5000
EOF
```

### 3. Create Gunicorn Config (Still as bfi-signals user)
```bash
cat > /home/bfi-signals/app/gunicorn.conf.py << 'EOF'
bind = "127.0.0.1:5000"
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 60
keepalive = 2
preload_app = True
EOF
```

### 4. Create Systemd Service (Run as root)
```bash
cat > /etc/systemd/system/bfi-signals.service << 'EOF'
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
EOF
```

### 5. Configure Nginx (Run as root)
```bash
cat > /etc/nginx/sites-available/bonangfinance << 'EOF'
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
        
        # Handle uploads
        location /uploads/ {
            alias /home/bfi-signals/app/core/uploads/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
}
EOF

# Enable site and remove default
ln -s /etc/nginx/sites-available/bonangfinance /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
```

### 6. Setup SSL Certificate (Run as root)
```bash
# Get SSL certificate
certbot --nginx -d bonangfinance.co.za -d www.bonangfinance.co.za --agree-tos --no-eff-email

# Test auto-renewal
certbot renew --dry-run
```

### 7. Start All Services (Run as root)
```bash
# Start application service
systemctl daemon-reload
systemctl enable bfi-signals.service
systemctl start bfi-signals.service

# Start nginx
systemctl enable nginx
systemctl restart nginx

# Setup firewall
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable
```

### 8. Setup GitHub Auto-Deploy SSH Key (Run as bfi-signals user)
```bash
sudo su - bfi-signals
ssh-keygen -t rsa -b 4096 -C "github-deploy" -f ~/.ssh/github_deploy -N ""
cat ~/.ssh/github_deploy.pub
# Copy this public key and add it to your GitHub repository Deploy Keys

# Setup SSH config
cat > ~/.ssh/config << 'EOF'
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_deploy
EOF

chmod 600 ~/.ssh/config
```

### 9. GitHub Repository Secrets Setup
Add these secrets to your GitHub repository (Settings > Secrets and variables > Actions):

- `VPS_HOST`: Your VPS IP address
- `VPS_USER`: `bfi-signals`
- `VPS_SSH_KEY`: Content of `/home/bfi-signals/.ssh/github_deploy` (private key)
- `VPS_PORT`: `22` (or your custom SSH port)

### 10. Test Deployment
```bash
# Check service status
systemctl status bfi-signals.service
systemctl status nginx

# Test locally
curl -I http://localhost:5000

# Test from outside
curl -I https://bonangfinance.co.za
```

## Important Configuration Changes

### Update .env file with your Discord webhook:
```bash
sudo su - bfi-signals
cd /home/bfi-signals/app
nano .env
# Update DISCORD_WEBHOOK_URL with your actual webhook
```

### Update GitHub repository URL:
```bash
# In step 2, replace with your actual repo:
git clone https://github.com/YOUR_USERNAME/bfi-signals.git .
```

## Monitoring Commands

### View logs:
```bash
# Application logs
sudo journalctl -u bfi-signals.service -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Restart services:
```bash
sudo systemctl restart bfi-signals.service
sudo systemctl reload nginx
```

## After Setup

1. Push any changes to your GitHub repository
2. The GitHub Action will automatically deploy to your VPS
3. Your site will be live at https://bonangfinance.co.za

🎉 **Your BFI Signals trading platform is now live with automatic deployments!**