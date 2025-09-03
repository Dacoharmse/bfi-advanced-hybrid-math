#!/bin/bash
# BFI Signals Local Development Sync Script
# Use this script on your LOCAL machine to push changes to VPS

set -e

echo "🔄 BFI Signals Local Development Sync"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration - UPDATE THESE FOR YOUR SETUP
VPS_HOST="server.bonangfinance.co.za"  # Your VPS hostname/IP
VPS_USER="root"                         # Your VPS username
VPS_PATH="/var/bfi-advanced-hybrid-math" # Project path on VPS
GITHUB_REPO="https://github.com/Dacoharmse/bfi-advanced-hybrid-math.git"

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

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    print_error "Not in a Git repository. Please run this from your project root."
    exit 1
fi

# Step 1: Check for uncommitted changes
if ! git diff --quiet || ! git diff --cached --quiet; then
    print_warning "You have uncommitted changes."
    echo "Uncommitted files:"
    git status --porcelain
    echo ""
    read -p "Do you want to commit these changes? (y/N): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Staging all changes..."
        git add .
        
        echo "Enter commit message:"
        read -r commit_message
        if [ -z "$commit_message" ]; then
            commit_message="Local development sync - $(date)"
        fi
        
        git commit -m "$commit_message"
        print_success "Changes committed"
    else
        print_error "Please commit or stash your changes before syncing."
        exit 1
    fi
fi

# Step 2: Push to GitHub
print_status "Pushing changes to GitHub..."
git push origin master
print_success "Changes pushed to GitHub"

# Step 3: Deploy to VPS
print_status "Deploying to VPS..."

# Check if we can connect to VPS
if ! ssh -o ConnectTimeout=10 "$VPS_USER@$VPS_HOST" "echo 'Connected'" 2>/dev/null; then
    print_error "Cannot connect to VPS. Please check:"
    echo "  - VPS_HOST: $VPS_HOST"
    echo "  - VPS_USER: $VPS_USER"
    echo "  - SSH key authentication is set up"
    exit 1
fi

# Execute deployment on VPS
ssh "$VPS_USER@$VPS_HOST" << EOF
set -e
echo "🚀 Executing deployment on VPS..."

cd "$VPS_PATH"
if [ ! -f "deploy.sh" ]; then
    echo "❌ deploy.sh not found on VPS. Please ensure the project is properly set up."
    exit 1
fi

# Make sure deploy script is executable
chmod +x deploy.sh

# Run deployment
./deploy.sh

echo "✅ VPS deployment completed"
EOF

if [ $? -eq 0 ]; then
    print_success "🎉 Sync completed successfully!"
    echo ""
    print_status "📋 What happened:"
    echo "   ✅ Local changes committed and pushed to GitHub"
    echo "   ✅ VPS pulled latest changes from GitHub"
    echo "   ✅ Dependencies updated on VPS"
    echo "   ✅ Configuration preserved"
    echo "   ✅ System checks completed"
    echo ""
    print_status "🌐 Your VPS is now running the latest version!"
    echo ""
    print_status "🔗 Access your dashboard:"
    echo "   http://$VPS_HOST:5000"
else
    print_error "❌ VPS deployment failed. Check the output above for details."
    exit 1
fi