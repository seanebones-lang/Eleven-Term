#!/bin/bash
# Install additional useful tools for Xcode and Android agents
# This script installs tools that enhance agent capabilities

set -e

echo "==========================================="
echo "🔧 Installing Additional Tools"
echo "==========================================="
echo ""

if ! command -v brew &> /dev/null; then
    echo "⚠️  Homebrew required for tool installation"
    exit 1
fi

# Function to install tool if missing
install_tool() {
    local tool=$1
    local formula=${2:-$tool}
    
    if command -v "$tool" &> /dev/null; then
        echo "✅ $tool: Already installed ($(which $tool))"
        return 0
    fi
    
    echo "❌ $tool: Not found"
    echo "   Installing $tool via Homebrew..."
    
    if brew install "$formula" 2>&1 | grep -q "Error"; then
        echo "⚠️  $tool: Installation failed or not available"
        return 1
    else
        if command -v "$tool" &> /dev/null; then
            echo "✅ $tool: Successfully installed"
            return 0
        else
            echo "⚠️  $tool: Installed but not in PATH"
            return 1
        fi
    fi
    echo ""
}

# Development tools
echo "📦 Installing Development Tools..."
echo ""

# CocoaPods (iOS/Mac dependency manager)
install_tool "pod" "cocoapods"

# Node.js and npm (useful for many projects)
install_tool "node" "node"
install_tool "npm" "node"  # npm comes with node

# Docker (containerization)
install_tool "docker" "docker"

# Git LFS (large file storage)
install_tool "git-lfs" "git-lfs"

# GitHub CLI
install_tool "gh" "gh"

# Additional system tools
echo ""
echo "🛠️  Installing System Tools..."
echo ""

# GNU coreutils (better versions of standard tools)
install_tool "gtimeout" "coreutils" || echo "   (coreutils available but gtimeout may have different name)"

# yt-dlp (useful for downloading content)
install_tool "yt-dlp" "yt-dlp" || echo "   (yt-dlp not installed)"

# wget (if not already available)
if ! command -v wget &> /dev/null; then
    install_tool "wget" "wget"
fi

# Python development tools
echo ""
echo "🐍 Installing Python Development Tools..."
echo ""

# poetry (Python dependency management)
install_tool "poetry" "poetry" || echo "   (poetry not installed - optional)"

# pyenv (Python version management)
install_tool "pyenv" "pyenv" || echo "   (pyenv not installed - optional)"

echo ""
echo "==========================================="
echo "✅ Additional Tool Installation Complete"
echo "==========================================="
echo ""
echo "Note: Some tools may require manual setup after installation"
echo "  - Docker: Requires Docker Desktop to be running"
echo "  - CocoaPods: Run 'pod setup' after installation"
echo "  - GitHub CLI: Run 'gh auth login' after installation"
echo ""
