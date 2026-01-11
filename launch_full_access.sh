#!/bin/bash
# Launch NextEleven Terminal Agent with full permissions and automatic sudo
# This script runs the agent with all safety prompts disabled
# The system will automatically use sudo when needed (for accessibility)
# Your sudo password will be stored securely in macOS Keychain (one-time setup)

cd "$(dirname "$0")"
python3 grok_agent.py --interactive --force --dangerously-skip-permissions "$@"
