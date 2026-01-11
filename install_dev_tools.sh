#!/bin/bash
# Install development-specific tools for Xcode and Android agents

set -e

echo "==========================================="
echo "🚀 Installing Development Tools"
echo "==========================================="
echo ""

if ! command -v brew &> /dev/null; then
    echo "⚠️  Homebrew required"
    exit 1
fi

install_if_missing() {
    local tool=$1
    local formula=${2:-$tool}
    
    if command -v "$tool" &> /dev/null; then
        echo "✅ $tool: Installed"
        return 0
    fi
    
    echo "❌ $tool: Installing..."
    brew install "$formula" 2>&1 | grep -v "^==>" | grep -v "^🍺" || true
    
    if command -v "$tool" &> /dev/null; then
        echo "✅ $tool: Installed successfully"
        return 0
    else
        echo "⚠️  $tool: Installation may have failed"
        return 1
    fi
}

# iOS/Mac development tools
echo "📱 iOS/Mac Development Tools:"
install_if_missing "pod" "cocoapods"
install_if_missing "carthage" "carthage" || echo "   (carthage: optional, not installed)"
install_if_missing "fastlane" "fastlane" || echo "   (fastlane: optional, not installed)"
echo ""

# General development tools
echo "🔧 General Development Tools:"
install_if_missing "gh" "gh"  # GitHub CLI
install_if_missing "git-lfs" "git-lfs"
install_if_missing "wget" "wget" || echo "   (wget: optional)"
echo ""

# Build tools
echo "🏗️  Build Tools:"
install_if_missing "cmake" "cmake" || echo "   (cmake: optional)"
install_if_missing "ninja" "ninja" || echo "   (ninja: optional)"
echo ""

echo "==========================================="
echo "✅ Development Tools Installation Complete"
echo "==========================================="
echo ""
