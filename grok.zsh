#!/usr/bin/env zsh
# Grok Terminal Agent - Zsh Plugin
# Provides prefix-triggered AI assistance in terminal

# Configuration
GROK_AGENT_DIR="$HOME/.grok-terminal"
GROK_AGENT_SCRIPT="$GROK_AGENT_DIR/grok_agent.py"
GROK_PREFIX="NextEleven AI:"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
RESET='\033[0m'

# Check if agent script exists
if [[ ! -f "$GROK_AGENT_SCRIPT" ]]; then
    echo "${RED}Error: Grok agent not found at $GROK_AGENT_SCRIPT${RESET}"
    echo "Run install.sh to install the agent."
    return 1
fi

# Function to handle Grok queries
_grok_handler() {
    local cmd="$1"
    
    # Check if command starts with prefix
    if [[ "$cmd" =~ ^"$GROK_PREFIX "(.*) ]]; then
        local query="${match[1]}"
        
        # Check for flags
        local no_log_flag=""
        local force_flag=""
        
        if [[ "$query" =~ --no-log ]]; then
            no_log_flag="--no-log"
            query="${query//--no-log/}"
            query="${query//  / }"  # Clean up double spaces
            query="${query## }"     # Trim leading space
            query="${query%% }"     # Trim trailing space
        fi
        
        if [[ "$query" =~ --force ]]; then
            force_flag="--force"
            query="${query//--force/}"
            query="${query//  / }"
            query="${query## }"
            query="${query%% }"
        fi
        
        # Call Python agent
        local output
        output=$(python3 "$GROK_AGENT_SCRIPT" "$query" $no_log_flag $force_flag 2>&1)
        local exit_code=$?
        
        # Print output (already includes streaming from Python)
        echo "$output"
        
        # Extract commands JSON if present
        if [[ "$output" =~ COMMANDS_JSON_START(.*)COMMANDS_JSON_END ]]; then
            local commands_json="${match[1]}"
            
            # Parse commands
            local commands
            local force_required
            
            # Use Python to parse JSON (more reliable than zsh)
            local parsed=$(python3 -c "
import json
import sys
try:
    data = json.loads('''$commands_json''')
    print('COMMANDS:' + '|'.join(data.get('commands', [])))
    print('FORCE:' + str(data.get('force_required', False)).lower())
except:
    pass
" 2>/dev/null)
            
            if [[ -n "$parsed" ]]; then
                # Extract commands
                if [[ "$parsed" =~ COMMANDS:(.*) ]]; then
                    commands="${match[1]}"
                fi
                
                # Extract force_required flag
                if [[ "$parsed" =~ FORCE:(.*) ]]; then
                    force_required="${match[1]}"
                fi
                
                if [[ -n "$commands" && "$commands" != "COMMANDS:" ]]; then
                    # Split commands by pipe
                    local cmd_array=("${(s:|:)commands}")
                    
                    if [[ ${#cmd_array[@]} -gt 1 ]]; then
                        # Multiple commands - use fzf for selection
                        echo ""
                        echo "${CYAN}Select a command to execute:${RESET}"
                        local selected=$(printf '%s\n' "${cmd_array[@]}" | fzf --height=40% --border --prompt="Command: ")
                        
                        if [[ -n "$selected" ]]; then
                            _grok_execute_command "$selected" "$force_required"
                        else
                            echo "${YELLOW}Cancelled${RESET}"
                        fi
                    else
                        # Single command
                        if [[ -n "$cmd_array[1]" ]]; then
                            _grok_execute_command "$cmd_array[1]" "$force_required"
                        fi
                    fi
                fi
            fi
        fi
        
        # Return exit code from Python script
        return $exit_code
    fi
}

# Function to safely execute commands
_grok_execute_command() {
    local cmd="$1"
    local force_required="$2"
    
    # Check if force is required but not provided
    # If force_required is true, it means the command is dangerous and user didn't provide --force
    if [[ "$force_required" == "true" ]]; then
        echo ""
        echo "${RED}This command requires the --force flag${RESET}"
        echo "${YELLOW}Usage: NextEleven AI: <query> --force${RESET}"
        return 1
    fi
    
    # Show preview
    echo ""
    echo "${CYAN}Preview:${RESET} Would run in ${CYAN}$(pwd)${RESET}"
    echo "${CYAN}Command:${RESET} $cmd"
    echo ""
    
    # Prompt for confirmation
    echo -n "${GREEN}Execute? [y/n/e(dit)]: ${RESET}"
    read -r response
    
    case "$response" in
        [Yy]|[Yy][Ee][Ss])
            echo "${GREEN}Executing...${RESET}"
            echo ""
            eval "$cmd"
            local exit_code=$?
            echo ""
            if [[ $exit_code -eq 0 ]]; then
                echo "${GREEN}✓ Command completed successfully${RESET}"
            else
                echo "${RED}✗ Command failed with exit code $exit_code${RESET}"
            fi
            ;;
        [Ee]|[Ee][Dd][Ii][Tt])
            # Edit command
            local edited_cmd=$(echo "$cmd" | vim -c 'set ft=sh' '+normal $' -)
            if [[ -n "$edited_cmd" && "$edited_cmd" != "$cmd" ]]; then
                echo "${CYAN}Executing edited command...${RESET}"
                echo ""
                eval "$edited_cmd"
            else
                echo "${YELLOW}Cancelled${RESET}"
            fi
            ;;
        *)
            echo "${YELLOW}Cancelled${RESET}"
            ;;
    esac
}

# Create NextEleven function to handle the prefix
# When user types "NextEleven AI: query", zsh will call NextEleven() with "AI:" and "query" as args
NextEleven() {
    # Reconstruct the full command from arguments
    # $@ will be "AI:" "query" "with" "multiple" "words"
    # We need to join them properly, handling the "AI:" prefix
    if [[ "$1" == "AI:" ]]; then
        # Skip the "AI:" and join the rest
        shift
        local query="$*"
        local full_cmd="$GROK_PREFIX $query"
    else
        # If "AI:" is missing, treat all args as the query
        local query="$*"
        local full_cmd="$GROK_PREFIX $query"
    fi
    _grok_handler "$full_cmd"
    return $?
}

# Also handle case where command_not_found_handler is called
# (fallback for edge cases)
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

# Export helper function for manual invocation
grok() {
    if [[ $# -eq 0 ]]; then
        echo "${CYAN}Usage: grok <query>${RESET}"
        echo "${CYAN}Example: grok 'list files in current directory'${RESET}"
        return 1
    fi
    
    local query="$*"
    _grok_handler "$GROK_PREFIX $query"
}

# Success message (only show once per session)
if [[ -z "$GROK_TERMINAL_LOADED" ]]; then
    export GROK_TERMINAL_LOADED=1
    # Silent load - user will see it when they use it
fi
