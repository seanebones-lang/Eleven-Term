#!/usr/bin/env python3
"""
Grok Terminal Agent - Python wrapper for xAI Grok API
Handles API communication, command validation, and session history
"""

import json
import os
import re
import sys
import subprocess
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
import httpx

# Configuration
API_ENDPOINT = "https://api.x.ai/v1/chat/completions"
MODEL = "grok-beta"
TEMPERATURE = 0.1
MAX_TOKENS = 2048
HISTORY_FILE = Path.home() / ".grok_terminal_history.json"
CONFIG_FILE = Path.home() / ".grok_terminal_config.json"
LOG_FILE = Path.home() / ".grok_terminal.log"

# Dangerous command patterns (require --force flag)
DANGEROUS_PATTERNS = [
    r'\brm\s+-rf\b',
    r'\bsudo\s+',
    r'\bkill\s+-9\b',
    r'\bmkfs\b',
    r'\bdd\s+if=',
    r'\bchmod\s+777\b',
    r'\>\s*/dev/',
    r'\bformat\b',
    r'\bfdisk\b',
    r'\bdel\s+/f\b',
]

# ANSI color codes
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
CYAN = '\033[0;36m'
RESET = '\033[0m'


def get_api_key() -> Optional[str]:
    """Retrieve API key from macOS Keychain"""
    try:
        result = subprocess.run(
            ['security', 'find-generic-password', '-s', 'grok-terminal', 
             '-a', 'xai-api-key', '-w'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def load_config() -> Dict[str, Any]:
    """Load configuration from file or return defaults"""
    defaults = {
        "model": MODEL,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "auto_log": True,
        "dangerous_commands_require_flag": True,
    }
    
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                user_config = json.load(f)
                defaults.update(user_config)
        except Exception:
            pass
    
    return defaults


def load_history() -> List[Dict[str, str]]:
    """Load conversation history"""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_history(messages: List[Dict[str, str]]):
    """Save conversation history"""
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(messages[-20:], f, indent=2)  # Keep last 20 messages
    except Exception:
        pass


def log_interaction(query: str, response: str, command: Optional[str] = None):
    """Log interaction to file"""
    config = load_config()
    if not config.get("auto_log", True):
        return
    
    try:
        with open(LOG_FILE, 'a') as f:
            log_entry = {
                "query": query,
                "response": response,
                "command": command,
                "timestamp": subprocess.run(['date', '-u', '+%Y-%m-%dT%H:%M:%SZ'], 
                                           capture_output=True, text=True).stdout.strip()
            }
            f.write(json.dumps(log_entry) + '\n')
    except Exception:
        pass


def classify_command_risk(command: str) -> tuple[str, str]:
    """
    Classify command risk level
    Returns: (level, color) where level is 'SAFE', 'CAUTION', or 'DANGEROUS'
    """
    command_lower = command.lower()
    
    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command_lower):
            return ('DANGEROUS', RED)
    
    # Caution: write operations
    caution_patterns = [
        r'\brm\b',
        r'\bmv\b',
        r'\bcp\b',
        r'\>',
        r'\|\s*tee\b',
        r'\bchmod\b',
        r'\bchown\b',
    ]
    
    for pattern in caution_patterns:
        if re.search(pattern, command_lower):
            return ('CAUTION', YELLOW)
    
    # Safe: read-only operations
    return ('SAFE', GREEN)


def get_offline_suggestions(query: str) -> str:
    """Provide local suggestions when offline"""
    query_lower = query.lower()
    
    # Extract potential command keywords
    common_commands = {
        'list': 'ls -la',
        'files': 'ls -la',
        'directory': 'ls -la',
        'find': 'find . -name',
        'search': 'grep -r',
        'grep': 'grep -r',
        'process': 'ps aux',
        'processes': 'ps aux',
        'disk': 'df -h',
        'space': 'du -sh *',
        'network': 'ifconfig',
        'git': 'git status',
        'status': 'git status',
        'permission': 'ls -la',
        'error': 'Check logs or man pages',
    }
    
    suggestions = []
    for keyword, cmd in common_commands.items():
        if keyword in query_lower:
            suggestions.append(f"Try: {cmd}")
            if len(suggestions) >= 3:
                break
    
    if not suggestions:
        # Generic suggestions based on query words
        words = query_lower.split()
        if words:
            first_word = words[0]
            suggestions.append(f"Try: man {first_word}")
            suggestions.append(f"Try: {first_word} --help")
    
    if not suggestions:
        suggestions = [
            "Try: man <command>",
            "Try: <command> --help",
            "Check system logs: tail -f /var/log/system.log"
        ]
    
    return f"""Offline - Unable to connect to API.

Local suggestions:
{chr(10).join('  • ' + s for s in suggestions)}

For more help, try:
  • man <command>
  • <command> --help
  • Check connection and try again"""


def extract_commands(response_text: str) -> List[str]:
    """Extract shell commands from AI response"""
    commands = []
    
    # Look for code blocks with shell/bash
    code_block_pattern = r'```(?:bash|sh|shell|zsh)?\n(.*?)```'
    matches = re.findall(code_block_pattern, response_text, re.DOTALL)
    for match in matches:
        # Split by newlines and filter out comments/empty lines
        lines = [line.strip() for line in match.split('\n')]
        commands.extend([line for line in lines if line and not line.startswith('#')])
    
    # Look for lines starting with $ or # (common command notation)
    dollar_pattern = r'^\$\s*(.+)$'
    for line in response_text.split('\n'):
        match = re.search(dollar_pattern, line)
        if match:
            cmd = match.group(1).strip()
            if cmd and not cmd.startswith('#'):
                commands.append(cmd)
    
    # If no commands found, try to find lines that look like commands
    if not commands:
        # Look for lines that are likely commands (contain common shell keywords)
        shell_keywords = ['ls', 'cd', 'find', 'grep', 'cat', 'echo', 'git', 'python', 'node']
        for line in response_text.split('\n'):
            stripped = line.strip()
            if any(keyword in stripped for keyword in shell_keywords) and len(stripped) < 200:
                # Check if it's not part of explanation text
                if not stripped.endswith('.') and not stripped.endswith(':'):
                    commands.append(stripped)
    
    return commands[:5]  # Limit to 5 suggestions


async def call_grok_api(query: str, api_key: str, config: Dict[str, Any], 
                       history: List[Dict[str, str]]) -> str:
    """Call xAI Grok API with streaming"""
    
    # Build messages from history + current query
    messages = history.copy()
    messages.append({"role": "user", "content": query})
    
    # Add system prompt
    system_prompt = """You are a helpful terminal assistant. When users ask for shell commands, provide:
1. A brief explanation
2. The exact command(s) to run in a code block
3. Any warnings about destructive operations

Format commands in ```bash code blocks. Be concise and accurate."""
    
    api_messages = [{"role": "system", "content": system_prompt}] + messages
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": config.get("model", MODEL),
        "messages": api_messages,
        "stream": True,
        "temperature": config.get("temperature", TEMPERATURE),
        "max_tokens": config.get("max_tokens", MAX_TOKENS),
    }
    
    full_response = ""
    retries = 3
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for attempt in range(retries):
            try:
                async with client.stream('POST', API_ENDPOINT, headers=headers, json=payload) as response:
                    if response.status_code == 429:
                        wait_time = 2 ** attempt
                        if attempt < retries - 1:
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            return "Error: Rate limit exceeded. Please try again later."
                    
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if not line.strip() or not line.startswith('data: '):
                            continue
                        
                        if line.strip() == 'data: [DONE]':
                            break
                        
                        try:
                            data = json.loads(line[6:])  # Remove 'data: ' prefix
                            if 'choices' in data and len(data['choices']) > 0:
                                delta = data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    print(content, end='', flush=True)
                                    full_response += content
                        except json.JSONDecodeError:
                            continue
                    
                    print()  # Newline after streaming
                    return full_response
                    
            except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                # After all retries failed, return None to trigger offline fallback
                return None
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    return "Error: Invalid API key. Run install.sh to update your key."
                return f"Error: API request failed ({e.response.status_code})"
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                # Check if it's a network-related error
                error_str = str(e).lower()
                if any(net_err in error_str for net_err in ['network', 'connection', 'resolve', 'timeout']):
                    return None  # Signal offline
                return f"Error: {str(e)}"
    
    return full_response if full_response else None  # Return None to trigger offline fallback


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: grok_agent.py <query> [--no-log] [--force]")
        sys.exit(1)
    
    query = sys.argv[1]
    no_log = '--no-log' in sys.argv
    force_flag = '--force' in sys.argv
    
    # Get API key
    api_key = get_api_key()
    if not api_key:
        print(f"{RED}Error: API key not found in Keychain.{RESET}")
        print("Run install.sh to set up your API key.")
        sys.exit(1)
    
    # Load config and history
    config = load_config()
    history = load_history()
    
    # Handle special commands
    if query.lower() == 'help':
        print(f"""{CYAN}Grok Terminal Agent - Available Commands{RESET}

{GREEN}Usage:{RESET} NextEleven AI: <your query>

{GREEN}Features:{RESET}
  • Command generation and explanation
  • Safe execution previews
  • Session history persistence
  • Streaming responses
  • Dangerous command detection

{GREEN}Examples:{RESET}
  NextEleven AI: list files in current directory
  NextEleven AI: explain this error: permission denied
  NextEleven AI: git status and suggest fixes

{GREEN}Flags:{RESET}
  --no-log    Disable logging to ~/.grok_terminal.log
  --force     Allow dangerous commands (use with caution)
""")
        sys.exit(0)
    
    # Call API
    try:
        response = asyncio.run(call_grok_api(query, api_key, config, history))
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Interrupted{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"{RED}Error: {str(e)}{RESET}")
        sys.exit(1)
    
    # Handle offline scenario
    if response is None:
        offline_msg = get_offline_suggestions(query)
        print(f"{YELLOW}{offline_msg}{RESET}")
        # Still try to extract commands from offline suggestions
        response = offline_msg
    
    if response.startswith("Error:"):
        print(f"{RED}{response}{RESET}")
        sys.exit(1)
    
    # Update history
    history.append({"role": "user", "content": query})
    history.append({"role": "assistant", "content": response})
    save_history(history)
    
    # Log interaction
    if not no_log:
        log_interaction(query, response)
    
    # Extract and display commands
    commands = extract_commands(response)
    
    if commands:
        print(f"\n{CYAN}{'='*60}{RESET}")
        print(f"{CYAN}Suggested command(s):{RESET}\n")
        
        for i, cmd in enumerate(commands, 1):
            risk_level, color = classify_command_risk(cmd)
            
            # Check if dangerous and force flag not set
            if risk_level == 'DANGEROUS' and not force_flag:
                print(f"{RED}⚠ DANGEROUS: {cmd}{RESET}")
                print(f"{YELLOW}  This command requires --force flag to execute{RESET}\n")
            else:
                print(f"{color}[{i}] {cmd}{RESET}")
                print(f"{BLUE}  Risk: {risk_level}{RESET}\n")
        
        # Output commands as JSON for zsh script to parse
        print(f"{CYAN}COMMANDS_JSON_START{RESET}")
        print(json.dumps({
            "commands": commands,
            "force_required": any(classify_command_risk(cmd)[0] == 'DANGEROUS' 
                                for cmd in commands) and not force_flag
        }))
        print(f"{CYAN}COMMANDS_JSON_END{RESET}")


if __name__ == "__main__":
    main()
