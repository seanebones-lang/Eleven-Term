#!/bin/bash
# One-click installer for NextEleven Terminal Agent (eleven edition, reverse-engineered from Claude Code)
# Verifies macOS Sonoma 14+, zsh, Python 3.12+, Homebrew, fzf, httpx, termcolor.
# Prompts for NextEleven API key, stores in Keychain.
# Copies files, adds to ~/.zshrc.

set -e

echo "Installing NextEleven Terminal Agent (eleven-powered, Claude Code reverse-engineer)..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check macOS version
MACOS_VERSION=$(sw_vers -productVersion | cut -d '.' -f1)
if [ "$MACOS_VERSION" -lt 14 ]; then
  echo -e "${RED}Error: Requires macOS Sonoma 14+${NC}"
  exit 1
fi
echo -e "${GREEN}✓ macOS $(sw_vers -productVersion) detected${NC}"

# Check zsh
if [ "$SHELL" != "/bin/zsh" ] && [ "$SHELL" != "/usr/bin/zsh" ]; then
  echo -e "${RED}Error: Requires zsh as default shell${NC}"
  exit 1
fi
echo -e "${GREEN}✓ zsh detected${NC}"

# Check Python 3.12+
if ! command -v python3 &> /dev/null; then
  echo -e "${YELLOW}Python 3 not found. Installing Python 3.12 via Homebrew...${NC}"
  if ! command -v brew &> /dev/null; then
    echo -e "${RED}Error: Homebrew required to install Python${NC}"
    exit 1
  fi
  brew install python@3.12
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 12 ]); then
  echo -e "${YELLOW}Python 3.12+ required. Current: $PYTHON_VERSION${NC}"
  echo -e "${YELLOW}Installing Python 3.12 via Homebrew...${NC}"
  if ! command -v brew &> /dev/null; then
    echo -e "${RED}Error: Homebrew required to install Python${NC}"
    exit 1
  fi
  brew install python@3.12
fi
echo -e "${GREEN}✓ Python $PYTHON_VERSION detected${NC}"

# Check/install Homebrew
if ! command -v brew &> /dev/null; then
  echo -e "${YELLOW}Homebrew not found. Installing Homebrew...${NC}"
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi
echo -e "${GREEN}✓ Homebrew detected${NC}"

# Install fzf
if ! command -v fzf &> /dev/null; then
  echo -e "${YELLOW}Installing fzf...${NC}"
  brew install fzf
fi
echo -e "${GREEN}✓ fzf detected${NC}"

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies (httpx, termcolor)...${NC}"
pip3 install --break-system-packages httpx termcolor 2>/dev/null || {
  # Try with pip if pip3 doesn't work
  python3 -m pip install --break-system-packages httpx termcolor
}
echo -e "${GREEN}✓ Python dependencies installed${NC}"

# Prompt for API key (if not already in Keychain)
KEYCHAIN_SERVICE="grok-terminal"
KEYCHAIN_ACCOUNT="xai-api-key"

if security find-generic-password -s "$KEYCHAIN_SERVICE" -a "$KEYCHAIN_ACCOUNT" &> /dev/null; then
  echo -e "${GREEN}✓ API key already stored in Keychain${NC}"
  read -p "Update API key? [y/N]: " update_key
  if [[ "$update_key" =~ ^[Yy]$ ]]; then
    read -sp "Enter NextEleven API key: " api_key
    echo ""
    if [ -z "$api_key" ]; then
      echo -e "${RED}Error: API key cannot be empty${NC}"
      exit 1
    fi
    # Delete old key
    security delete-generic-password -s "$KEYCHAIN_SERVICE" -a "$KEYCHAIN_ACCOUNT" &> /dev/null || true
    # Add new key
    security add-generic-password -s "$KEYCHAIN_SERVICE" -a "$KEYCHAIN_ACCOUNT" -w "$api_key" -U
    echo -e "${GREEN}✓ API key updated${NC}"
  fi
else
  read -sp "Enter NextEleven API key: " api_key
  echo ""
  if [ -z "$api_key" ]; then
    echo -e "${RED}Error: API key cannot be empty${NC}"
    exit 1
  fi
  security add-generic-password -s "$KEYCHAIN_SERVICE" -a "$KEYCHAIN_ACCOUNT" -w "$api_key" -U
  echo -e "${GREEN}✓ API key stored in Keychain${NC}"
fi

# Create directories (exact specification)
INSTALL_DIR="$HOME/.grok_terminal"
HOOKS_DIR="$HOME/.grok_terminal/hooks"
TODOS_DIR="$HOME/.grok_terminal"  # todos.json goes in main dir

echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p "$INSTALL_DIR"
mkdir -p "$HOOKS_DIR"
# Todos dir is same as install dir
echo -e "${GREEN}✓ Directories created${NC}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Copy files
echo -e "${YELLOW}Copying files...${NC}"
if [ ! -f "$SCRIPT_DIR/grok_agent.py" ]; then
  echo -e "${RED}Error: grok_agent.py not found in $SCRIPT_DIR${NC}"
  exit 1
fi

cp "$SCRIPT_DIR/grok_agent.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/grok.zsh" "$INSTALL_DIR/" 2>/dev/null || {
  echo -e "${YELLOW}Warning: grok.zsh not found, skipping...${NC}"
}

# Copy security_utils.py if it exists
if [ -f "$SCRIPT_DIR/security_utils.py" ]; then
  cp "$SCRIPT_DIR/security_utils.py" "$INSTALL_DIR/"
  chmod +x "$INSTALL_DIR/security_utils.py"
fi

# Make Python script executable
chmod +x "$INSTALL_DIR/grok_agent.py"

echo -e "${GREEN}✓ Files copied to $INSTALL_DIR${NC}"

# Set secure permissions on installation directory
chmod 700 "$INSTALL_DIR"
chmod 755 "$HOOKS_DIR"

# Add to ~/.zshrc
ZSHRC="$HOME/.zshrc"
SOURCE_LINE="source $INSTALL_DIR/grok.zsh"

if grep -q "$INSTALL_DIR/grok.zsh" "$ZSHRC" 2>/dev/null; then
  echo -e "${GREEN}✓ Already configured in ~/.zshrc${NC}"
else
  echo "" >> "$ZSHRC"
  echo "# NextEleven Terminal Agent (eleven-powered)" >> "$ZSHRC"
  echo "$SOURCE_LINE" >> "$ZSHRC"
  echo -e "${GREEN}✓ Added to ~/.zshrc${NC}"
fi

echo ""
echo -e "${GREEN}=== Installation Complete! ===${NC}"
echo -e "${CYAN}Usage:${NC}"
echo -e "  ${YELLOW}Interactive mode:${NC} Type 'eleven' to start"
echo -e "  ${YELLOW}Prefix mode:${NC} Type 'NextEleven AI: <your query>'"
echo -e ""
echo -e "${YELLOW}Run 'source ~/.zshrc' or open a new terminal to activate.${NC}"
echo -e "${YELLOW}Type 'eleven' to start interactive mode (Claude-like).${NC}"
echo ""
