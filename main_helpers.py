"""
Helper functions extracted from main() for better organization
"""
import sys
import json
import os
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

# Import from grok_agent (avoid circular imports)
try:
    from grok_agent import (
        colored, get_api_key, load_config, load_history, save_history, save_todos,
        load_todos, call_grok_api, extract_tools, classify_command_risk, run_hook,
        get_env_context, get_system_prompt, TOOLS, DEFAULT_CONFIG, HISTORY_COMPACT_THRESHOLD,
        COMPACT_PROMPT, TOPIC_PROMPT
    )
except ImportError:
    # Fallback if imported before grok_agent is fully loaded
    pass

def handle_list_agents(config: Dict[str, Any]) -> None:
    """Handle --list-agents flag"""
    specialized_agents = config.get("specialized_agents", DEFAULT_CONFIG.get("specialized_agents", {}))
    print(colored(f"\n📋 Available Specialized Agents ({len(specialized_agents)}):", 'cyan'))
    print("")
    for agent_id, agent_info in sorted(specialized_agents.items()):
        emoji = agent_info.get('emoji', '🤖')
        name = agent_info.get('name', agent_id)
        print(f"  {emoji} {colored(agent_id, 'yellow'):<20} - {name}")
    print("")
    print(colored("Usage:", 'cyan'))
    print("  eleven --model security --endpoint https://grokcode.vercel.app/api/chat")
    print("  eleven --model performance --endpoint https://grokcode.vercel.app/api/chat")
    print("  eleven --list-agents  # Show this list")
    print("")
    sys.exit(0)

def handle_slash_commands(user_input: str, api_key: str, config: Dict[str, Any], history: List[Dict[str, str]]) -> bool:
    """Handle slash commands (/help, /init, /clear, /hooks)
    
    Returns:
        True if command was handled, False otherwise
    """
    if not user_input.startswith('/'):
        return False
    
    if user_input == '/help':
        print(colored("Commands:", 'cyan'))
        print("  /init  - Generate ELEVEN.md with project instructions/tools")
        print("  /clear - Reset conversation history")
        print("  /hooks - Configure hooks (see ~/.grok_terminal/hooks/ for details)")
        return True
    elif user_input == '/init':
        try:
            init_resp = call_grok_api(
                api_key,
                [{"role": "user", "content": "Generate ELEVEN.md with project instructions/tools."}],
                config['model'],
                config['temperature'],
                config['max_tokens'],
                stream=False,
                config=config
            )
            init_content = init_resp.get('choices', [{}])[0].get('message', {}).get('content', '')
            with open('ELEVEN.md', 'w') as f:
                f.write(init_content)
            print(colored("ELEVEN.md generated.", 'green'))
        except Exception as e:
            print(colored(f"Failed to generate ELEVEN.md: {e}", 'red'))
        return True
    elif user_input == '/clear':
        history.clear()
        cwd, git_status, dir_tree = get_env_context()
        system_prompt = get_system_prompt(cwd, git_status, dir_tree)
        history.append({"role": "system", "content": system_prompt})
        print(colored("History cleared.", 'green'))
        return True
    elif user_input == '/hooks':
        hook_dir = os.path.expanduser(DEFAULT_CONFIG['hooks_dir'])
        print(colored(f"Hooks directory: {hook_dir}", 'cyan'))
        print("Create PreToolUse.sh and PostToolUse.sh in this directory")
        return True
    
    return False

def execute_tool_safely(
    tool_name: str,
    params: Dict[str, Any],
    args: Any,
    history: List[Dict[str, str]]
) -> Tuple[int, str, str]:
    """Execute tool with safety checks and hooks
    
    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    if tool_name not in TOOLS:
        return 1, "", f"Unknown tool: {tool_name}"
    
    # Classify risk for Bash commands
    risk = classify_command_risk(params.get('command', '')) if tool_name == 'Bash' else "SAFE"
    
    # Pre-hook
    pre_ok, pre_out = run_hook("PreToolUse", {"tool": tool_name, "params": params})
    if not pre_ok:
        print(colored(f"Pre-hook failed: {pre_out}", 'red'))
        return 1, "", pre_out
    
    # Permission prompt (unless skipped)
    if not args.dangerously_skip_permissions and risk != "SAFE" and not args.force:
        print(colored(f"Allow {tool_name} with params {params}? [y/n]", 'yellow'))
        if input().lower() != 'y':
            return 0, "", "Cancelled by user"
    
    # Execute tool
    try:
        if tool_name == 'Bash':
            exit_code, stdout, stderr = TOOLS[tool_name](params, allow_force=args.force)
        else:
            exit_code, stdout, stderr = TOOLS[tool_name](params)
        
        result_text = stdout if stdout else stderr
        
        if exit_code == 0:
            print(colored(f"Tool {tool_name} result: {result_text}", 'magenta'))
        else:
            print(colored(f"Tool {tool_name} error: {result_text}", 'red'))
        
        # Post-hook
        if exit_code is not None:
            run_hook("PostToolUse", {"tool": tool_name, "result": result_text if exit_code == 0 else stderr})
        
        return exit_code, stdout, stderr
    except Exception as e:
        print(colored(f"Tool {tool_name} exception: {e}", 'red'))
        return 1, "", str(e)

def compact_history_if_needed(history: List[Dict[str, str]], api_key: str, config: Dict[str, Any]) -> List[Dict[str, str]]:
    """Compact history if it exceeds threshold
    
    Returns:
        Compacted history list
    """
    if len(history) <= HISTORY_COMPACT_THRESHOLD:
        return history
    
    try:
        compact_resp = call_grok_api(
            api_key,
            [{"role": "user", "content": COMPACT_PROMPT.format(history=json.dumps(history[1:]))}],
            config['model'],
            config['temperature'],
            1024,
            stream=False,
            config=config
        )
        compacted_content = compact_resp.get('choices', [{}])[0].get('message', {}).get('content', '')
        return [history[0]] + [{"role": "assistant", "content": compacted_content}]
    except Exception:
        # If compaction fails, just keep recent history
        return history[:1] + history[-19:]

def initialize_interactive_session(api_key: str, config: Dict[str, Any], history: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Initialize interactive session with history compaction if needed
    
    Returns:
        Initialized history list
    """
    # Quota check
    try:
        quota_resp = call_grok_api(
            api_key,
            [{"role": "user", "content": "quota"}],
            config['model'],
            0.0,
            10,
            stream=False,
            config=config
        )
        if "error" in quota_resp:
            print(colored("Quota/API issue.", 'red'))
            sys.exit(1)
    except Exception as e:
        print(colored(f"API check failed: {e}", 'red'))
        # Continue anyway
    
    # Summarize previous if history exists
    system_msg = None
    if history and len(history) > 2:
        try:
            compact_resp = call_grok_api(
                api_key,
                [{"role": "user", "content": COMPACT_PROMPT.format(history=json.dumps(history))}],
                config['model'],
                config['temperature'],
                512,
                stream=False,
                config=config
            )
            compacted_content = compact_resp.get('choices', [{}])[0].get('message', {}).get('content', '')
            cwd, git_status, dir_tree = get_env_context()
            system_prompt = get_system_prompt(cwd, git_status, dir_tree)
            history = [
                {"role": "system", "content": system_prompt},
                {"role": "assistant", "content": compacted_content}
            ]
        except Exception:
            # If compaction fails, use full history
            cwd, git_status, dir_tree = get_env_context()
            system_prompt = get_system_prompt(cwd, git_status, dir_tree)
            history = [{"role": "system", "content": system_prompt}] + history
    else:
        cwd, git_status, dir_tree = get_env_context()
        system_prompt = get_system_prompt(cwd, git_status, dir_tree)
        history = [{"role": "system", "content": system_prompt}]
    
    return history

def run_interactive_loop(
    api_key: str,
    config: Dict[str, Any],
    history: List[Dict[str, str]],
    todos: Dict[str, Any],
    args: Any
) -> None:
    """Run the interactive session loop"""
    print(colored("eleven session started. Type queries; /help for commands; 'exit' to quit.", 'green'))
    
    while True:
        try:
            user_input = input(colored("You: ", 'blue')).strip()
            
            if user_input.lower() == 'exit':
                save_history(history)
                save_todos(todos)
                print(colored("Session ended.", 'green'))
                break
            
            # Handle slash commands
            if handle_slash_commands(user_input, api_key, config, history):
                continue
            
            # Topic detection
            is_new_topic = False
            try:
                topic_resp = call_grok_api(
                    api_key,
                    [{"role": "user", "content": TOPIC_PROMPT.format(input=user_input)}],
                    config['model'],
                    0.0,
                    128,
                    stream=False,
                    config=config
                )
                topic_content = topic_resp.get('choices', [{}])[0].get('message', {}).get('content', '{}')
                topic = json.loads(topic_content)
                if topic.get('isNewTopic', False):
                    is_new_topic = True
                    print(colored(f"New topic: {topic.get('title', 'Unknown')}", 'cyan'))
            except Exception:
                pass  # Topic detection is non-critical
            
            # Add user message to history
            history.append({"role": "user", "content": user_input})
            
            # Update system prompt with current context
            cwd, git_status, dir_tree = get_env_context()
            system_prompt = get_system_prompt(cwd, git_status, dir_tree)
            if history and history[0].get('role') == 'system':
                history[0]['content'] = system_prompt
            else:
                history.insert(0, {"role": "system", "content": system_prompt})
            
            # Call API with streaming
            messages = history
            full_response = ""
            print(colored("eleven: ", 'green'), end='', flush=True)
            
            try:
                for chunk in call_grok_api(api_key, messages, config['model'], config['temperature'], config['max_tokens'], stream=True, config=config):
                    content = chunk.get('choices', [{}])[0].get('delta', {}).get('content', '')
                    if content:
                        print(content, end='', flush=True)
                        full_response += content
                print()  # Newline after streaming
            except Exception as e:
                print(colored(f"\nAPI error: {e}", 'red'))
                continue
            
            # Add assistant response to history
            history.append({"role": "assistant", "content": full_response})
            
            # Extract and execute tools
            tool_calls = extract_tools(full_response)
            for tool_name, params_list in tool_calls:
                params = {p[0]: p[1] for p in params_list}
                execute_tool_safely(tool_name, params, args, history)
            
            # Compact history if too long
            history = compact_history_if_needed(history, api_key, config)
            
            # Todos if mentioned
            if "todo" in user_input.lower():
                todos[datetime.now().isoformat()] = user_input
                save_todos(todos)
            
            # Save history periodically
            save_history(history)
            
        except KeyboardInterrupt:
            print(colored("\nInterrupted. Session ended.", 'yellow'))
            save_history(history)
            save_todos(todos)
            break
        except EOFError:
            print(colored("\nEOF. Session ended.", 'yellow'))
            save_history(history)
            save_todos(todos)
            break