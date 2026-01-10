#!/bin/bash
# Grok Terminal Agent - One-Click Installer
# Verifies prerequisites and sets up the Grok terminal integration

set -e

INSTALL_DIR="$HOME/.grok-terminal"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Grok Terminal Agent Installer ===${NC}\n"

# 1. Check macOS version (Sonoma 14+)
echo -e "${YELLOW}[1/7]${NC} Checking macOS version..."
MACOS_VERSION=$(sw_vers -productVersion | cut -d. -f1)
if [ "$MACOS_VERSION" -lt 14 ]; then
    echo -e "${RED}✗ macOS Sonoma 14+ required. Current: $(sw_vers -productVersion)${NC}"
    exit 1
fi
echo -e "${GREEN}✓ macOS $(sw_vers -productVersion) detected${NC}"

# 2. Check zsh as default shell
echo -e "${YELLOW}[2/7]${NC} Checking shell..."
if [ "$SHELL" != "/bin/zsh" ] && [ "$SHELL" != "/usr/bin/zsh" ]; then
    echo -e "${RED}✗ zsh required. Current: $SHELL${NC}"
    exit 1
fi
echo -e "${GREEN}✓ zsh detected${NC}"

# 3. Check Python 3.12+
echo -e "${YELLOW}[3/7]${NC} Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 12 ]); then
    echo -e "${RED}✗ Python 3.12+ required. Current: $PYTHON_VERSION${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $PYTHON_VERSION detected${NC}"

# 4. Check Homebrew
echo -e "${YELLOW}[4/7]${NC} Checking Homebrew..."
if ! command -v brew &> /dev/null; then
    echo -e "${RED}✗ Homebrew not found. Install from https://brew.sh${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Homebrew detected${NC}"

# 5. Install fzf if missing
echo -e "${YELLOW}[5/7]${NC} Checking fzf..."
if ! command -v fzf &> /dev/null; then
    echo -e "${YELLOW}  Installing fzf via Homebrew...${NC}"
    brew install fzf
else
    echo -e "${GREEN}✓ fzf already installed${NC}"
fi

# 6. Install httpx
echo -e "${YELLOW}[6/7]${NC} Installing Python dependencies..."
python3 -m pip install --user httpx --quiet
echo -e "${GREEN}✓ httpx installed${NC}"

# 7. Setup API key in Keychain
echo -e "${YELLOW}[7/7]${NC} Setting up API key..."
KEYCHAIN_SERVICE="grok-terminal"
KEYCHAIN_ACCOUNT="xai-api-key"

# Check if key already exists
if security find-generic-password -s "$KEYCHAIN_SERVICE" -a "$KEYCHAIN_ACCOUNT" &> /dev/null; then
    echo -e "${GREEN}✓ API key already stored in Keychain${NC}"
    read -p "Update API key? [y/N]: " update_key
    if [[ ! "$update_key" =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}Skipping API key update${NC}"
    else
        # Remove old key
        security delete-generic-password -s "$KEYCHAIN_SERVICE" -a "$KEYCHAIN_ACCOUNT" &> /dev/null || true
        # Prompt for new key
        read -sp "Enter your xAI API key: " api_key
        echo ""
        if [ -z "$api_key" ]; then
            echo -e "${RED}✗ API key cannot be empty${NC}"
            exit 1
        fi
        security add-generic-password -s "$KEYCHAIN_SERVICE" -a "$KEYCHAIN_ACCOUNT" -w "$api_key" -U
        echo -e "${GREEN}✓ API key updated${NC}"
    fi
else
    read -sp "Enter your xAI API key: " api_key
    echo ""
    if [ -z "$api_key" ]; then
        echo -e "${RED}✗ API key cannot be empty${NC}"
        exit 1
    fi
    security add-generic-password -s "$KEYCHAIN_SERVICE" -a "$KEYCHAIN_ACCOUNT" -w "$api_key" -U
    echo -e "${GREEN}✓ API key stored in Keychain${NC}"
fi

# 8. Create installation directory
echo -e "\n${YELLOW}Installing files...${NC}"
mkdir -p "$INSTALL_DIR"

# Copy files
cp "$SCRIPT_DIR/grok_agent.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/grok.zsh" "$INSTALL_DIR/"

# Make Python script executable
chmod +x "$INSTALL_DIR/grok_agent.py"

echo -e "${GREEN}✓ Files installed to $INSTALL_DIR${NC}"

# 9. Add to ~/.zshrc
ZSHRC="$HOME/.zshrc"
SOURCE_LINE="source $INSTALL_DIR/grok.zsh"

if grep -q "$INSTALL_DIR/grok.zsh" "$ZSHRC" 2>/dev/null; then
    echo -e "${GREEN}✓ Already configured in ~/.zshrc${NC}"
else
    echo "" >> "$ZSHRC"
    echo "# Grok Terminal Agent" >> "$ZSHRC"
    echo "$SOURCE_LINE" >> "$ZSHRC"
    echo -e "${GREEN}✓ Added to ~/.zshrc${NC}"
fi

echo -e "\n${GREEN}=== Installation Complete! ===${NC}"
echo -e "${YELLOW}Run 'source ~/.zshrc' or open a new terminal to activate.${NC}"
echo -e "${YELLOW}Usage: NextEleven AI: <your query>${NC}\n"
