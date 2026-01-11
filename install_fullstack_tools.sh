#!/bin/bash
# Install full stack development tools
# Adds database clients, API tools, cloud CLI, and other full stack essentials

set -e

echo "==========================================="
echo "📦 FULL STACK DEVELOPMENT TOOLS INSTALLER"
echo "==========================================="
echo ""

if ! command -v brew &> /dev/null; then
    echo "⚠️  Homebrew required"
    exit 1
fi

install_tool() {
    local tool=$1
    local install_cmd=$2
    local importance=${3:-"Medium"}
    
    if command -v "$tool" &> /dev/null; then
        echo "  ✅ $tool: Already installed"
        return 0
    fi
    
    echo "  ❌ $tool: Installing ($importance priority)..."
    
    if eval "$install_cmd" > /dev/null 2>&1; then
        if command -v "$tool" &> /dev/null; then
            echo "  ✅ $tool: Installed successfully"
            return 0
        fi
    fi
    
    echo "  ⚠️  $tool: Installation failed or not available"
    return 1
}

# Database Tools
echo "🗄️  Installing Database Tools..."
install_tool "mysql" "brew install mysql-client" "High"
install_tool "psql" "brew install postgresql@15" "High"
install_tool "mongosh" "brew install mongosh" "Medium"
install_tool "redis-cli" "brew install redis" "Medium"
# sqlite3 is typically already installed on macOS
if command -v sqlite3 &> /dev/null; then
    echo "  ✅ sqlite3: Already installed (system)"
else
    echo "  ⚠️  sqlite3: Not found (usually pre-installed on macOS)"
fi
echo ""

# API Tools
echo "🌐 Installing API Tools..."
install_tool "httpie" "brew install httpie" "High"
echo ""

# Cloud CLI Tools
echo "☁️  Installing Cloud CLI Tools..."
install_tool "aws" "brew install awscli" "High"
install_tool "gcloud" "brew install google-cloud-sdk" "Medium"
install_tool "terraform" "brew install terraform" "Medium"
install_tool "kubectl" "brew install kubectl" "Medium"
echo ""

# Node.js Tools
echo "📦 Installing Node.js Tools..."
if command -v npm &> /dev/null; then
    install_tool "pm2" "npm install -g pm2" "Medium"
    install_tool "nodemon" "npm install -g nodemon" "Low"
else
    echo "  ⚠️  npm not found - skipping Node.js tools"
fi
echo ""

# Code Quality Tools
echo "✨ Installing Code Quality Tools..."
if command -v npm &> /dev/null; then
    install_tool "eslint" "npm install -g eslint" "Medium" || echo "  (eslint: install manually if needed)"
    install_tool "prettier" "npm install -g prettier" "Medium" || echo "  (prettier: install manually if needed)"
else
    echo "  ⚠️  npm not found - skipping code quality tools"
fi
echo ""

echo "==========================================="
echo "✅ FULL STACK TOOLS INSTALLATION COMPLETE"
echo "==========================================="
echo ""
echo "📋 Summary:"
echo ""
echo "Database Tools:"
echo "  • MySQL, PostgreSQL, MongoDB, Redis clients"
echo ""
echo "API Tools:"
echo "  • HTTPie for better API testing"
echo ""
echo "Cloud CLI:"
echo "  • AWS CLI, Google Cloud SDK, Terraform, Kubernetes"
echo ""
echo "Node.js Tools:"
echo "  • PM2 (process manager), nodemon (auto-restart)"
echo ""
echo "Note: Some tools may require additional configuration:"
echo "  • Cloud CLI tools: Run 'aws configure', 'gcloud init', etc."
echo "  • Database clients: Configure connection credentials"
echo "  • PM2: Run 'pm2 startup' to enable process management"
echo ""
