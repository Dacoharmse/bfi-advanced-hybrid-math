#!/bin/bash
# BFI Signals Deployment Script
# Syncs changes from GitHub and updates the VPS deployment

set -e  # Exit on any error

echo "🚀 BFI Signals Deployment Script"
echo "================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/var/bfi-advanced-hybrid-math"
BACKUP_DIR="/var/bfi-backups/$(date +%Y%m%d_%H%M%S)"
VENV_DIR="$PROJECT_DIR/venv"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -d "$PROJECT_DIR" ]; then
    print_error "Project directory not found: $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR"

print_status "Starting deployment process..."

# Step 1: Backup current configuration
print_status "Creating backup of current configuration..."
mkdir -p "$BACKUP_DIR"
if [ -f ".env" ]; then
    cp ".env" "$BACKUP_DIR/.env.backup"
    print_success "Environment file backed up"
fi

if [ -f "core/ai_learning.db" ]; then
    cp "core/ai_learning.db" "$BACKUP_DIR/ai_learning.db.backup"
    print_success "Database backed up"
fi

# Step 2: Stash any local changes
print_status "Stashing local changes..."
git add .
if git diff --cached --quiet; then
    print_status "No local changes to stash"
else
    git stash push -m "Pre-deployment stash $(date)"
    print_success "Local changes stashed"
fi

# Step 3: Fetch and pull latest changes
print_status "Fetching latest changes from GitHub..."
git fetch origin

print_status "Pulling latest changes..."
git pull origin master
print_success "Code updated from GitHub"

# Step 4: Handle environment file
if [ ! -f ".env" ]; then
    if [ -f "$BACKUP_DIR/.env.backup" ]; then
        print_warning ".env file missing, restoring from backup..."
        cp "$BACKUP_DIR/.env.backup" ".env"
        print_success "Environment file restored"
    else
        print_warning ".env file missing, creating template..."
        cat > .env << 'EOF'
# BFI Signals Configuration
# Discord Integration
DISCORD_WEBHOOK_URL=your_discord_webhook_url_here

# API Keys (if needed)
# GEMINI_API_KEY=your_api_key_here

# Database Configuration
DATABASE_URL=sqlite:///ai_learning.db

# Application Settings
FLASK_ENV=production
DEBUG=False
EOF
        print_warning "Please update .env file with your actual configuration"
    fi
fi

# Step 5: Install/Update Python dependencies
print_status "Checking Python virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
fi

print_status "Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
print_success "Dependencies updated"

# Step 6: Database migration (if needed)
if [ -f "$BACKUP_DIR/ai_learning.db.backup" ] && [ ! -f "core/ai_learning.db" ]; then
    print_status "Restoring database from backup..."
    cp "$BACKUP_DIR/ai_learning.db.backup" "core/ai_learning.db"
    print_success "Database restored"
fi

# Step 7: Set proper permissions
print_status "Setting file permissions..."
chmod +x deploy.sh
chmod +x start_dashboard.sh 2>/dev/null || true
chmod +x scripts/*.py 2>/dev/null || true
print_success "Permissions updated"

# Step 8: Test critical components
print_status "Running system checks..."

# Test Discord connection
if [ -f "debug_discord.py" ]; then
    print_status "Testing Discord connection..."
    if python3 debug_discord.py | grep -q "Discord is properly configured"; then
        print_success "Discord connection test passed"
    else
        print_warning "Discord may need configuration"
    fi
fi

# Test Python imports
print_status "Testing Python imports..."
if python3 -c "import flask, requests, pandas, sqlite3; print('✅ All imports successful')" 2>/dev/null; then
    print_success "Python dependencies check passed"
else
    print_warning "Some Python dependencies may be missing"
fi

# Step 9: Show deployment summary
echo ""
print_success "🎉 Deployment completed successfully!"
echo "================================="
echo ""
print_status "📋 Deployment Summary:"
echo "   • Code updated from GitHub"
echo "   • Dependencies installed/updated"
echo "   • Configuration preserved"
echo "   • Database backed up and restored"
echo "   • System checks completed"
echo ""
print_status "🚀 Next Steps:"
echo "   • Start dashboard: python3 core/dashboard.py"
echo "   • Or use launcher: ./start_dashboard.sh"
echo "   • Check logs for any issues"
echo ""
print_status "📁 Backup Location: $BACKUP_DIR"
echo ""

deactivate 2>/dev/null || true

print_success "Deployment script completed! 🎯"