# Deploy BFI Signals to Existing WordPress VPS

## 🌐 Deployment Options for bonangfinance.co.za

Since your domain already has WordPress + SSL, choose one of these deployment strategies:

### Option 1: Subdomain Deployment (Recommended)
Deploy at: **`app.bonangfinance.co.za`** or **`trading.bonangfinance.co.za`**

### Option 2: Path-based Deployment  
Deploy at: **`bonangfinance.co.za/app`** or **`bonangfinance.co.za/trading`**

### Option 3: Port-based Deployment
Deploy at: **`bonangfinance.co.za:5000`**

---

## 🚀 Option 1: Subdomain Deployment (RECOMMENDED)

### Step 1: DNS Setup
```bash
# Add A record in your DNS provider:
# trading.bonangfinance.co.za → Your VPS IP
```

### Step 2: VPS Setup Commands
```bash
# 1. Install dependencies (as root)
apt update && apt install -y python3 python3-pip python3-venv supervisor

# 2. Create application user
useradd -m -s /bin/bash bfi-signals
usermod -aG www-data bfi-signals

# 3. Setup application (as bfi-signals user)
sudo su - bfi-signals
mkdir -p /home/bfi-signals/app
cd /home/bfi-signals/app
git clone https://github.com/Dacoharmse/bfi-advanced-hybrid-math.git .
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# 4. Create environment file
cat > .env << 'EOF'
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your_super_secret_production_key_change_this
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL
TRADING_SYMBOLS=^NDX
USE_ENHANCED_DISCORD=true
HOST=0.0.0.0
PORT=5000
EOF

# 5. Create Gunicorn config
cat > gunicorn.conf.py << 'EOF'
bind = "127.0.0.1:5001"
workers = 3
timeout = 60
preload_app = True
user = "bfi-signals"
group = "www-data"
EOF
```

### Step 3: System Service (as root)
```bash
cat > /etc/systemd/system/bfi-signals.service << 'EOF'
[Unit]
Description=BFI Signals Flask Application
After=network.target

[Service]
User=bfi-signals
Group=www-data
WorkingDirectory=/home/bfi-signals/app
Environment=PATH=/home/bfi-signals/app/venv/bin
ExecStart=/home/bfi-signals/app/venv/bin/gunicorn --config gunicorn.conf.py core.dashboard:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable bfi-signals.service
systemctl start bfi-signals.service
```

### Step 4: Nginx Configuration (as root)
```bash
# Add to existing nginx config or create new site
cat > /etc/nginx/sites-available/bfi-trading << 'EOF'
server {
    listen 80;
    server_name trading.bonangfinance.co.za;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name trading.bonangfinance.co.za;
    
    # SSL configuration (use existing certificates or create new ones)
    ssl_certificate /etc/letsencrypt/live/bonangfinance.co.za/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bonangfinance.co.za/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://127.0.0.1:5001;
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
}
EOF

# Enable site and reload nginx
ln -s /etc/nginx/sites-available/bfi-trading /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

### Step 5: SSL Certificate for Subdomain
```bash
# Add subdomain to existing certificate
certbot --nginx -d trading.bonangfinance.co.za
```

---

## 🚀 Option 2: Path-based Deployment

### Step 1: Setup Application (Same as Option 1, Steps 2-3)

### Step 2: Modify WordPress Nginx Config
```bash
# Edit your existing WordPress nginx config
# Add this location block BEFORE the WordPress location blocks:

location /trading/ {
    proxy_pass http://127.0.0.1:5001/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_redirect off;
    
    location /trading/static/ {
        alias /home/bfi-signals/app/core/static/;
        expires 1y;
    }
}

# Then reload nginx
nginx -t && systemctl reload nginx
```

### Step 3: Update Flask App for Path Prefix
```bash
# Edit core/dashboard.py to handle path prefix
sudo su - bfi-signals
cd /home/bfi-signals/app
nano core/dashboard.py

# Add this after app = Flask(__name__):
app.config['APPLICATION_ROOT'] = '/trading'
```

---

## 🚀 Option 3: Port-based Deployment (Simple)

### Step 1: Setup Application (Steps 2-3 from Option 1)
Use port 5000 in gunicorn.conf.py:
```python
bind = "0.0.0.0:5000"
```

### Step 2: Open Firewall Port
```bash
ufw allow 5000
```

### Access: `https://bonangfinance.co.za:5000`

---

## 🔄 GitHub Auto-Deploy Setup

### Step 1: SSH Key for GitHub Actions
```bash
# As bfi-signals user
sudo su - bfi-signals
ssh-keygen -t rsa -b 4096 -C "github-deploy" -f ~/.ssh/github_deploy -N ""
cat ~/.ssh/github_deploy.pub
# Add this public key to your GitHub repo Deploy Keys

# Show private key for GitHub Secrets
cat ~/.ssh/github_deploy
```

### Step 2: GitHub Repository Secrets
Add these to: https://github.com/Dacoharmse/bfi-advanced-hybrid-math/settings/secrets/actions

- `VPS_HOST`: Your VPS IP address
- `VPS_USER`: `bfi-signals`  
- `VPS_SSH_KEY`: Content of `/home/bfi-signals/.ssh/github_deploy`
- `VPS_PORT`: `22`

### Step 3: Update GitHub Actions Workflow
The workflow is already created and will auto-deploy when you push to master.

---

## 🛠️ Quick Setup Commands (Copy-Paste Ready)

### For Subdomain Deployment:
```bash
# Run as root
apt update && apt install -y python3 python3-pip python3-venv supervisor && useradd -m -s /bin/bash bfi-signals && usermod -aG www-data bfi-signals

# Run as bfi-signals user  
sudo su - bfi-signals && mkdir -p /home/bfi-signals/app && cd /home/bfi-signals/app && git clone https://github.com/Dacoharmse/bfi-advanced-hybrid-math.git . && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && pip install gunicorn

# Create configs (run each separately)
cat > .env << 'EOF'
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your_super_secret_production_key_change_this
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL
TRADING_SYMBOLS=^NDX
USE_ENHANCED_DISCORD=true
HOST=0.0.0.0
PORT=5000
EOF

cat > gunicorn.conf.py << 'EOF'
bind = "127.0.0.1:5001"
workers = 3
timeout = 60
preload_app = True
EOF
```

## 🔍 Testing & Verification

### Check Service Status:
```bash
systemctl status bfi-signals.service
journalctl -u bfi-signals.service -f
```

### Test Endpoints:
```bash
# Local test
curl -I http://127.0.0.1:5001

# Public test (replace with your chosen option)
curl -I https://trading.bonangfinance.co.za
curl -I https://bonangfinance.co.za/trading/
curl -I https://bonangfinance.co.za:5000
```

## 📋 Final Notes

1. **Update Discord Webhook** in the `.env` file
2. **Choose one deployment option** that fits your needs
3. **Test thoroughly** before going live
4. **Monitor logs** for any issues
5. **Push changes** to GitHub for auto-deployment

Your BFI Signals trading platform will be live alongside your existing WordPress site! 🚀