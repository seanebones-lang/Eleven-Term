#!/bin/bash
# Install missing tools required by Xcode and Android Expert Agents
# This script checks for and installs tools that enhance agent capabilities

set -e

echo "==========================================="
echo "🔧 Installing Missing Tools for Agents"
echo "==========================================="
echo ""

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "⚠️  Homebrew not found. Some tools require Homebrew."
    echo "   Install Homebrew: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    echo ""
fi

# Function to install tool if missing
install_if_missing() {
    local tool=$1
    local install_cmd=$2
    
    if command -v "$tool" &> /dev/null; then
        echo "✅ $tool: Already installed ($(which $tool))"
        return 0
    fi
    
    echo "❌ $tool: Not found"
    echo "   Installing $tool..."
    
    if command -v brew &> /dev/null; then
        eval "$install_cmd"
        if command -v "$tool" &> /dev/null; then
            echo "✅ $tool: Successfully installed"
        else
            echo "⚠️  $tool: Installation may have failed (check manually)"
        fi
    else
        echo "⚠️  Skipping $tool (Homebrew required)"
    fi
    echo ""
}

# Essential development tools
echo "📦 Installing Essential Tools..."
echo ""

# fzf - Fuzzy finder (used in grok.zsh)
install_if_missing "fzf" "brew install fzf"

# tree - Directory tree viewer (used in get_env_context)
install_if_missing "tree" "brew install tree"

# jq - JSON processor (useful for parsing API responses, config files)
install_if_missing "jq" "brew install jq"

# Xcode Command Line Tools (if not installed)
echo "📱 Checking Xcode Tools..."
if ! command -v xcodebuild &> /dev/null; then
    echo "❌ Xcode Command Line Tools: Not found"
    echo "   Installing Xcode Command Line Tools..."
    xcode-select --install 2>/dev/null || echo "   Run: xcode-select --install"
else
    echo "✅ Xcode Command Line Tools: Installed"
fi
echo ""

# Swift (should come with Xcode)
if ! command -v swift &> /dev/null; then
    echo "⚠️  Swift: Not found (install Xcode Command Line Tools)"
else
    echo "✅ Swift: Installed ($(which swift))"
fi
echo ""

# Android tools (these are usually installed with Android Studio)
echo "🤖 Checking Android Tools..."
echo ""

# Note: Android tools (adb, emulator, gradle) are typically installed with Android Studio
# and managed through Android SDK. We detect them in android_utils.py
# If Android Studio is installed, these should be available via ANDROID_HOME

if [ -n "$ANDROID_HOME" ]; then
    echo "✅ ANDROID_HOME: $ANDROID_HOME"
    if [ -f "$ANDROID_HOME/platform-tools/adb" ]; then
        echo "✅ ADB: Available at $ANDROID_HOME/platform-tools/adb"
    else
        echo "⚠️  ADB: Not found in $ANDROID_HOME/platform-tools/"
    fi
    
    if [ -f "$ANDROID_HOME/emulator/emulator" ]; then
        echo "✅ Emulator: Available at $ANDROID_HOME/emulator/emulator"
    else
        echo "⚠️  Emulator: Not found in $ANDROID_HOME/emulator/"
    fi
else
    echo "⚠️  ANDROID_HOME: Not set"
    echo "   Install Android Studio and set ANDROID_HOME environment variable"
    echo "   Default location: ~/Library/Android/sdk"
fi
echo ""

# Gradle (can be installed standalone or comes with Android projects)
if ! command -v gradle &> /dev/null; then
    echo "⚠️  Gradle: Not in PATH"
    echo "   Note: Gradle wrapper (gradlew) in projects works without global install"
    echo "   To install: brew install gradle"
else
    echo "✅ Gradle: Installed ($(which gradle))"
fi
echo ""

# Python packages (check requirements-dev.txt)
echo "🐍 Checking Python Dependencies..."
if command -v pip3 &> /dev/null; then
    echo "✅ pip3: Available"
    echo "   Install dev dependencies: pip3 install -r requirements-dev.txt"
else
    echo "⚠️  pip3: Not found"
fi
echo ""

# Additional useful tools
echo "🛠️  Installing Additional Useful Tools..."
echo ""

# ripgrep - Fast grep alternative (better than grep for large codebases)
install_if_missing "rg" "brew install ripgrep"

# bat - Better cat (syntax highlighting)
install_if_missing "bat" "brew install bat"

# fd - Better find (faster than find)
install_if_missing "fd" "brew install fd"

# htop - Better top (process monitoring)
install_if_missing "htop" "brew install htop"

echo "==========================================="
echo "✅ Tool Installation Complete"
echo "==========================================="
echo ""
echo "Summary:"
echo "  Essential tools checked and installed"
echo "  Xcode tools: Check Xcode Command Line Tools"
echo "  Android tools: Check Android Studio installation"
echo "  Python dependencies: Run 'pip3 install -r requirements-dev.txt'"
echo ""
