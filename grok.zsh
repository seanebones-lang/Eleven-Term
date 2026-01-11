#!/usr/bin/env zsh
# NextEleven Terminal Agent - Zsh Plugin
# eleven-powered, reverse-engineered from Claude Code
# Provides prefix-triggered AI assistance and interactive mode

# Configuration
GROK_AGENT_DIR="$HOME/.grok_terminal"
GROK_AGENT_SCRIPT="$GROK_AGENT_DIR/grok_agent.py"
GROK_PREFIX="NextEleven AI:"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
RESET='\033[0m'

# Check if agent script exists
if [[ ! -f "$GROK_AGENT_SCRIPT" ]]; then
    echo "${RED}Error: eleven agent not found at $GROK_AGENT_SCRIPT${RESET}"
    echo "Run install.sh to install the agent."
    return 1
fi

# Prefix handler for "NextEleven AI: <query>"
_grok_prefix_handler() {
    local query="${1#${GROK_PREFIX}}"
    query="${query## }"  # Trim leading space
    
    # Check for flags
    local flags=()
    if [[ "$query" =~ --no-log ]]; then
        flags+=("--no-log")
        query="${query//--no-log/}"
        query="${query//  / }"
        query="${query## }"
        query="${query%% }"
    fi
    
    if [[ "$query" =~ --force ]]; then
        flags+=("--force")
        query="${query//--force/}"
        query="${query//  / }"
        query="${query## }"
        query="${query%% }"
    fi
    
    # Call Python agent in non-interactive mode
    python3 "$GROK_AGENT_SCRIPT" "$query" "${flags[@]}"
    return $?
}

# Function to handle Grok queries (called from NextEleven function)
_grok_handler() {
    local cmd="$1"
    
    # Check if command starts with prefix
    if [[ "$cmd" =~ ^"$GROK_PREFIX "(.*) ]]; then
        local query="${match[1]}"
        _grok_prefix_handler "$GROK_PREFIX $query"
        return $?
    fi
}

# NextEleven function for prefix-triggered interaction
# Usage: NextEleven AI: <your query>
NextEleven() {
    if [[ "$1" == "AI:" ]]; then
        shift
        local query="$*"
        local full_cmd="$GROK_PREFIX $query"
    else
        local query="$*"
        local full_cmd="$GROK_PREFIX $query"
    fi
    _grok_handler "$full_cmd"
    return $?
}

# Interactive launcher (type 'eleven')
# Usage: eleven [--dangerously-skip-permissions] [--no-log] [--force] [--model MODEL_NAME] [--config CONFIG_PATH] [--endpoint URL]
eleven() {
    local flags=()
    
    # Parse flags
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dangerously-skip-permissions)
                flags+=("--dangerously-skip-permissions")
                shift
                ;;
            --no-log)
                flags+=("--no-log")
                shift
                ;;
            --force)
                flags+=("--force")
                shift
                ;;
            --model)
                flags+=("--model" "$2")
                shift 2
                ;;
            --config)
                flags+=("--config" "$2")
                shift 2
                ;;
            --endpoint)
                flags+=("--endpoint" "$2")
                shift 2
                ;;
            *)
                # Unknown flag or argument
                break
                ;;
        esac
    done
    
    # Call Python agent in interactive mode
    python3 "$GROK_AGENT_SCRIPT" --interactive "${flags[@]}"
    return $?
}

# Safe execution wrapper (called from Python for command execution)
# This is used when tools need to execute commands with confirmation
_grok_execute_command() {
    local cmd="$1"
    local dir="${2:-$(pwd)}"
    local risk="${3:-CAUTION}"
    local force="${4:-}"
    
    echo "${CYAN}Preview:${RESET} Would run in ${CYAN}$dir${RESET}"
    echo "${CYAN}Command:${RESET} $cmd"
    echo "${CYAN}Risk:${RESET} $risk"
    
    if [[ "$risk" == "DANGEROUS" && "$force" != "--force" ]]; then
        echo "${RED}Requires --force for dangerous commands.${RESET}"
        return 1
    fi
    
    echo -n "${GREEN}Execute? [y/n/e(dit)]: ${RESET}"
    read -r choice
    
    case "$choice" in
        [Yy]|[Yy][Ee][Ss])
            # Use security_utils.py for safe execution if available
            local security_script="$GROK_AGENT_DIR/security_utils.py"
            if [[ -f "$security_script" ]]; then
                cd "$dir" && python3 "$security_script" "$cmd" $force 2>&1
                local exit_code=$?
            else
                # Fallback: use Python subprocess for safer execution (still not ideal but better than eval)
                cd "$dir" && python3 -c "
import subprocess
import shlex
import sys
try:
    args = shlex.split(sys.argv[1])
    result = subprocess.run(args, shell=False, capture_output=True, text=True, timeout=60)
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    sys.exit(result.returncode)
except:
    # Last resort: shell execution (less safe but functional)
    result = subprocess.run(sys.argv[1], shell=True, capture_output=True, text=True, timeout=60)
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    sys.exit(result.returncode)
" "$cmd" 2>&1
                local exit_code=$?
            fi
            
            if [[ $exit_code -eq 0 ]]; then
                echo "${GREEN}✓ Command completed.${RESET}"
            else
                echo "${RED}✗ Command failed with exit code $exit_code${RESET}"
            fi
            return $exit_code
            ;;
        [Ee]|[Ee][Dd][Ii][Tt])
            # Edit command
            local tmpfile=$(mktemp /tmp/grok_cmd_XXXXXX)
            echo "$cmd" > "$tmpfile"
            vim "$tmpfile"
            local edited_cmd=$(cat "$tmpfile")
            rm "$tmpfile"
            
            if [[ -n "$edited_cmd" && "$edited_cmd" != "$cmd" ]]; then
                echo "${CYAN}Executing edited command...${RESET}"
                # Recursive call with edited command
                _grok_execute_command "$edited_cmd" "$dir" "$risk" "$force"
            else
                echo "${YELLOW}Cancelled${RESET}"
            fi
            ;;
        *)
            echo "${YELLOW}Cancelled${RESET}"
            return 1
            ;;
    esac
}

# fzf for multi-command selection (if multiple commands suggested)
_grok_select_command() {
    echo "$1" | fzf --multi --height=40% --border --prompt="Select command(s): "
}

# Command not found handler (fallback)
command_not_found_handler() {
    local cmd="$1"
    
    # If someone tries to run "NextEleven" without "AI:", show usage
    if [[ "$cmd" == "NextEleven" ]]; then
        echo "${CYAN}Usage: NextEleven AI: <your query>${RESET}"
        echo "${CYAN}Example: NextEleven AI: list files${RESET}"
        return 1
    fi
    
    # Not our command, show normal error
    echo "zsh: command not found: $cmd" >&2
    return 127
}

# Success message (only show once per session)
if [[ -z "$GROK_TERMINAL_LOADED" ]]; then
    export GROK_TERMINAL_LOADED=1
    # Silent load - user will see it when they use it
fi
