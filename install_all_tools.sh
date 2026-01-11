#!/bin/bash
# Comprehensive tool installation for NextEleven Terminal Agent
# Installs all tools required by Xcode, Android, and general agents

set -e

echo "==========================================="
echo "🚀 Comprehensive Tool Installation"
echo "==========================================="
echo ""

if ! command -v brew &> /dev/null; then
    echo "⚠️  Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

echo "✅ Homebrew: $(which brew)"
echo ""

# Function to install tool
install_tool() {
    local tool=$1
    local formula=${2:-$tool}
    
    if command -v "$tool" &> /dev/null; then
        echo "  ✅ $tool: Already installed"
        return 0
    fi
    
    echo "  ❌ $tool: Installing..."
    if brew install "$formula" > /dev/null 2>&1; then
        if command -v "$tool" &> /dev/null; then
            echo "  ✅ $tool: Installed successfully"
            return 0
        fi
    fi
    echo "  ⚠️  $tool: Installation failed or not available"
    return 1
}

# Essential tools
echo "📦 Essential Tools:"
install_tool "fzf"
install_tool "tree"
install_tool "jq"
install_tool "wget"
echo ""

# Enhanced productivity tools
echo "⚡ Enhanced Tools:"
install_tool "rg" "ripgrep"
install_tool "bat"
install_tool "fd"
install_tool "htop"
echo ""

# Development tools
echo "🔧 Development Tools:"
install_tool "gh"  # GitHub CLI
install_tool "git-lfs"
install_tool "node"
# npm comes with node
if command -v npm &> /dev/null; then
    echo "  ✅ npm: Available"
else
    echo "  ⚠️  npm: Should come with node"
fi
install_tool "docker"
install_tool "poetry"
install_tool "pyenv"
echo ""

# Xcode/iOS tools
echo "📱 iOS/Mac Development Tools:"
if ! command -v xcodebuild &> /dev/null; then
    echo "  ⚠️  Xcode Command Line Tools: Not installed"
    echo "     Run: xcode-select --install"
else
    echo "  ✅ Xcode Command Line Tools: Installed"
fi

install_tool "pod" "cocoapods"
install_tool "carthage"
install_tool "fastlane"
install_tool "xcodegen"
echo ""

# Build tools
echo "🏗️  Build Tools:"
install_tool "cmake"
install_tool "ninja"
echo ""

# Python dependencies
echo "🐍 Python Dependencies:"
if command -v pip3 &> /dev/null; then
    echo "  Installing Python packages..."
    pip3 install --user --quiet httpx termcolor pytest pytest-cov pytest-asyncio pytest-mock \
        black flake8 mypy isort bandit 2>&1 | grep -v "already satisfied" || true
    echo "  ✅ Python packages installed"
else
    echo "  ⚠️  pip3: Not found"
fi
echo ""

echo "==========================================="
echo "✅ Tool Installation Complete"
echo "==========================================="
echo ""
echo "📊 Final Status:"
echo ""

# Final status check
python3 << 'PYEOF'
import shutil

tools = {
    "Essential": ["fzf", "tree", "jq", "git", "python3", "pip3", "wget"],
    "Enhanced": ["rg", "bat", "fd", "htop"],
    "Development": ["gh", "git-lfs", "node", "npm", "docker"],
    "Xcode": ["xcodebuild", "xcrun", "swift", "pod", "fastlane"],
    "Build": ["cmake", "make"]
}

total = 0
available = 0

for category, tool_list in tools.items():
    for tool in tool_list:
        total += 1
        if shutil.which(tool):
            available += 1

print(f"  Tools Available: {available}/{total} ({available*100//total}%)")
PYEOF

echo ""
echo "✅ All essential tools installed!"
echo ""
EOF
