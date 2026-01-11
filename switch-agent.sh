#!/bin/bash
# Agent Switcher - Switch between specialized agents
# Usage: switch-agent [agent-name] or switch-agent --list

CONFIG_DIR="$HOME/.grok_terminal"
MAIN_CONFIG="$HOME/.grok_terminal_config.json"

# List available agents
list_agents() {
    echo "Available agents:"
    echo ""
    if [ -f "$MAIN_CONFIG" ]; then
        current_model=$(grep -o '"model"[[:space:]]*:[[:space:]]*"[^"]*"' "$MAIN_CONFIG" | head -1 | cut -d'"' -f4)
        echo "  Current: $current_model"
    fi
    echo ""
    echo "To switch agents:"
    echo "  switch-agent <agent-name>"
    echo ""
    echo "Or use --model flag:"
    echo "  eleven --model your-agent-name"
}

# Switch to specific agent
switch_agent() {
    local agent_name="$1"
    
    if [ -z "$agent_name" ]; then
        echo "Error: Agent name required"
        echo "Usage: switch-agent <agent-name>"
        echo "       switch-agent --list"
        return 1
    fi
    
    # Create or update config with specified model
    if [ -f "$MAIN_CONFIG" ]; then
        # Update existing config
        python3 << EOF
import json
import sys

try:
    with open("$MAIN_CONFIG", 'r') as f:
        config = json.load(f)
except:
    config = {}

config['model'] = "$agent_name"

with open("$MAIN_CONFIG", 'w') as f:
    json.dump(config, f, indent=2)

print("Switched to agent: $agent_name")
EOF
    else
        # Create new config
        cat > "$MAIN_CONFIG" << EOF
{
  "model": "$agent_name",
  "temperature": 0.1,
  "max_tokens": 2048
}
EOF
        echo "Created config and switched to agent: $agent_name"
    fi
    
    chmod 600 "$MAIN_CONFIG"
    echo "✅ Agent switched! Run 'eleven' to use it."
}

# Main
case "$1" in
    --list|-l)
        list_agents
        ;;
    "")
        list_agents
        ;;
    *)
        switch_agent "$1"
        ;;
esac
