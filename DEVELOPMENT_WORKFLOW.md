# BFI Signals Development Workflow

This guide explains how to sync your local development environment with the VPS using Git.

## 🏗️ Architecture Overview

```
Local Development ──➤ GitHub Repository ──➤ VPS Production
     (Your PC)              (Git Repo)         (Live Server)
```

## 📋 Initial Setup

### 1. Set Up Local Environment

On your **local machine**:

```bash
# Clone the repository
git clone https://github.com/Dacoharmse/bfi-advanced-hybrid-math.git
cd bfi-advanced-hybrid-math

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your local configuration
```

### 2. Configure SSH Access to VPS

Make sure you can SSH to your VPS without password:

```bash
# Test SSH connection
ssh root@server.bonangfinance.co.za

# If you need to set up SSH keys:
ssh-copy-id root@server.bonangfinance.co.za
```

### 3. Update Sync Script Configuration

Edit `sync-local.sh` on your local machine:

```bash
# Update these variables:
VPS_HOST="server.bonangfinance.co.za"  # Your VPS hostname/IP
VPS_USER="root"                         # Your VPS username
VPS_PATH="/var/bfi-advanced-hybrid-math" # Project path on VPS
```

## 🔄 Daily Development Workflow

### Development on Local Machine

1. **Make your changes** in your local development environment
2. **Test locally** - run the dashboard locally to ensure everything works
3. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

### Deploy to VPS

4. **Sync to VPS** using the automated script:
   ```bash
   chmod +x sync-local.sh
   ./sync-local.sh
   ```

This script will:
- ✅ Push your changes to GitHub
- ✅ Pull changes on the VPS
- ✅ Update dependencies
- ✅ Preserve configuration
- ✅ Run system checks
- ✅ Create backups

## 🛠️ Available Scripts

### On Local Machine

- **`sync-local.sh`** - Main sync script (push to GitHub + deploy to VPS)
- **`git push origin master`** - Push changes to GitHub only

### On VPS

- **`deploy.sh`** - Pull latest changes and update VPS
- **`python3 core/dashboard.py`** - Start the dashboard
- **`debug_discord.py`** - Test Discord connection

## 🔧 Manual Operations

### Manual Deploy on VPS

If you need to manually update the VPS:

```bash
# SSH to VPS
ssh root@server.bonangfinance.co.za

# Navigate to project
cd /var/bfi-advanced-hybrid-math

# Run deployment script
./deploy.sh
```

### Manual Git Operations

```bash
# Check status
git status

# Pull specific branch
git pull origin branch-name

# View commit history
git log --oneline -10

# Stash changes temporarily
git stash
git stash pop  # Restore stashed changes
```

## 📁 File Management

### Files Ignored by Git (`.gitignore`)
- `.env` files (environment configuration)
- Database files (`*.db`)
- Log files (`*.log`)
- Virtual environment (`venv/`)
- Temporary files

### Files Synchronized
- All source code (`.py`, `.html`, `.css`, `.js`)
- Configuration templates (`.env.example`)
- Documentation (`.md`)
- Requirements (`requirements.txt`)

## 🔐 Environment Configuration

### Local Development
- Create `.env` file with your local settings
- Use local Discord webhook for testing
- Point to local database

### VPS Production
- Maintains separate `.env` file with production settings
- Uses production Discord webhook
- Uses production database

### Sharing Configuration
- **Never commit** `.env` files to Git
- Use `.env.example` as template
- Update production `.env` manually when needed

## 🚨 Troubleshooting

### Sync Script Issues

**Problem**: SSH connection fails
```bash
# Test SSH manually
ssh root@server.bonangfinance.co.za

# Check SSH key
ssh-add -l
```

**Problem**: Git push fails
```bash
# Check git status
git status

# Check remote
git remote -v

# Fix remote URL if needed
git remote set-url origin https://github.com/Dacoharmse/bfi-advanced-hybrid-math.git
```

### VPS Issues

**Problem**: Deploy script fails
```bash
# SSH to VPS and check
cd /var/bfi-advanced-hybrid-math
git status
./deploy.sh
```

**Problem**: Dependencies missing
```bash
# On VPS, reinstall dependencies
cd /var/bfi-advanced-hybrid-math
source venv/bin/activate
pip install -r requirements.txt
```

## 🎯 Best Practices

### Development
1. **Test locally** before syncing
2. **Commit frequently** with clear messages
3. **Use branches** for major features
4. **Keep VPS environment stable** - don't develop directly on VPS

### Security
1. **Never commit** sensitive data (API keys, passwords)
2. **Use environment variables** for configuration
3. **Keep backups** of important data
4. **Update dependencies** regularly

### Deployment
1. **Use the sync script** - don't deploy manually unless necessary
2. **Check logs** after deployment
3. **Monitor Discord** for any issues
4. **Keep production stable** - test in local first

## 📊 Monitoring

### Check System Status
```bash
# On VPS - check if dashboard is running
ps aux | grep python

# Check logs
tail -f core/*.log

# Test Discord connection
python3 debug_discord.py
```

### Health Checks
The deployment script automatically runs system checks:
- Discord connection test
- Python dependencies check
- Database integrity check
- File permissions check

## 🔄 Advanced Workflows

### Feature Branches
For major features, use Git branches:

```bash
# Create feature branch
git checkout -b feature/new-trading-algorithm

# Work on feature
# ... make changes ...

# Commit and push feature
git add .
git commit -m "Add new trading algorithm"
git push origin feature/new-trading-algorithm

# Merge to master when ready
git checkout master
git merge feature/new-trading-algorithm
git push origin master

# Deploy to VPS
./sync-local.sh
```

### Rollback Strategy
If something goes wrong:

```bash
# On VPS - check git log
git log --oneline -5

# Rollback to previous commit
git reset --hard COMMIT_HASH
./deploy.sh

# Or restore from backup
cp /var/bfi-backups/TIMESTAMP/ai_learning.db.backup core/ai_learning.db
```

This workflow ensures your local development and VPS stay synchronized while maintaining proper version control and deployment practices.