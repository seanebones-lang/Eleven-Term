#!/usr/bin/env python3
"""
Ralph-Wiggum Loop Implementation for Eleven-Term
Enables self-iterative AI loops for autonomous development workflows
"""

import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)


def extract_tools_from_natural_language(response: str) -> List[Tuple[str, List[Tuple[str, str]]]]:
    """Extract tool calls from natural language responses (fallback for orchestrator API)
    
    Parses patterns like:
    - "Tool: ls" or "Tool: LS"
    - "Use LS tool" or "Use the View tool"
    - "Tool Request: Bash" or "Execute: ls -la"
    - "I need to use the View tool to read file.txt"
    """
    tools = []
    
    # Normalize response for easier parsing
    response_lower = response.lower()
    
    # Pattern 1: "Tool: <name>", "Tool Request: <name>", "🔧 Tool Request", etc.
    tool_pattern1 = r'(?:tool\s*(?:request)?:?\s*|use\s+(?:the\s+)?|execute\s+)(ls|view|edit|write|bash|grep|glob)(?:\s+tool)?'
    matches1 = list(re.finditer(tool_pattern1, response_lower, re.IGNORECASE))
    
    # Also catch emoji patterns like "🔧 Tool Request"
    emoji_pattern = r'[🔧⚙️🛠️]\s*(?:tool\s*(?:request)?:?\s*)?(ls|view|edit|write|bash|grep|glob)'
    emoji_matches = list(re.finditer(emoji_pattern, response_lower, re.IGNORECASE))
    matches1 = matches1 + emoji_matches
    
    for match in matches1:
        tool_name = match.group(1).upper()
        if tool_name == "LS":
            tools.append(("LS", [("path", ".")]))
        elif tool_name in ["VIEW", "EDIT", "WRITE"]:
            # Try to find file path nearby
            context_start = max(0, match.start() - 50)
            context_end = min(len(response), match.end() + 100)
            context = response[context_start:context_end]
            
            # Look for file paths
            file_pattern = r'(?:file|path|read|write|edit)\s+(?:to\s+|from\s+)?([a-zA-Z0-9_./-]+\.(?:py|js|ts|jsx|tsx|json|md|txt|yml|yaml|toml|rs|go|java|kt|swift|cpp|c|h|hpp|rb|php|sh|bash|zsh|fish)|[a-zA-Z0-9_./-]+/[a-zA-Z0-9_./-]+)'
            file_match = re.search(file_pattern, context, re.IGNORECASE)
            if file_match:
                file_path = file_match.group(1).strip()
                if tool_name == "VIEW":
                    tools.append(("View", [("path", file_path)]))
                elif tool_name == "EDIT":
                    tools.append(("Edit", [("path", file_path)]))
                elif tool_name == "WRITE":
                    # For write, we'd need content - skip for now
                    pass
        elif tool_name == "BASH":
            # Try to find command
            context_start = max(0, match.start() - 50)
            context_end = min(len(response), match.end() + 150)
            context = response[context_start:context_end]
            
            # Look for command patterns
            cmd_patterns = [
                r'(?:command|execute|run):\s*([^\n]+)',
                r'`([^`]+)`',
                r'"([^"]+)"',
                r'(?:run|execute)\s+([a-zA-Z0-9_./-]+\s+[^\n]+)'
            ]
            for pattern in cmd_patterns:
                cmd_match = re.search(pattern, context, re.IGNORECASE)
                if cmd_match:
                    cmd = cmd_match.group(1).strip()
                    if len(cmd) < 200:  # Sanity check
                        tools.append(("Bash", [("command", cmd)]))
                        break
    
    # Pattern 2: Explicit XML-like mentions that aren't properly formatted
    xml_like = r'<tool\s+name=["\']?(\w+)["\']?>'
    xml_matches = re.finditer(xml_like, response, re.IGNORECASE)
    for match in xml_matches:
        tool_name = match.group(1).upper()
        # Try to extract params from surrounding context
        context_start = match.start()
        context_end = min(len(response), match.end() + 200)
        context = response[context_start:context_end]
        
        if tool_name == "LS":
            path_match = re.search(r'(?:path|dir|directory)[=:]\s*["\']?([^"\'\s]+)', context, re.IGNORECASE)
            path = path_match.group(1) if path_match else "."
            tools.append(("LS", [("path", path)]))
        elif tool_name == "VIEW":
            path_match = re.search(r'(?:path|file)[=:]\s*["\']?([^"\'\s]+)', context, re.IGNORECASE)
            if path_match:
                tools.append(("View", [("path", path_match.group(1))]))
        elif tool_name == "BASH":
            cmd_match = re.search(r'(?:command|cmd)[=:]\s*["\']?([^"\']+)', context, re.IGNORECASE)
            if cmd_match:
                tools.append(("Bash", [("command", cmd_match.group(1).strip())]))
    
    # Pattern 3: Direct action statements
    # "List files in current directory" -> LS
    if re.search(r'list\s+(?:all\s+)?(?:files|directory|dir)', response_lower):
        if not any(t[0] == "LS" for t in tools):
            tools.append(("LS", [("path", ".")]))
    
    # "Read file X" or "View file X" -> View
    read_match = re.search(r'(?:read|view|open)\s+(?:the\s+)?(?:file\s+)?([a-zA-Z0-9_./-]+\.(?:py|js|ts|jsx|tsx|json|md|txt|yml|yaml|toml|rs|go|java|kt|swift|cpp|c|h|hpp|rb|php|sh|bash|zsh|fish)|[a-zA-Z0-9_./-]+/[a-zA-Z0-9_./-]+)', response_lower)
    if read_match and not any(t[0] == "View" for t in tools):
        tools.append(("View", [("path", read_match.group(1))]))
    
    # Deduplicate tools (keep first occurrence)
    seen = set()
    unique_tools = []
    for tool_name, params in tools:
        key = (tool_name, tuple(sorted(params)))
        if key not in seen:
            seen.add(key)
            unique_tools.append((tool_name, params))
    
    return unique_tools

# Loop state file location
LOOP_STATE_DIR = os.path.expanduser('~/.grok_terminal/loops')
LOOP_LOG_DIR = os.path.expanduser('~/.grok_terminal/loop_logs')

# Ensure directories exist
os.makedirs(LOOP_STATE_DIR, exist_ok=True)
os.makedirs(LOOP_LOG_DIR, exist_ok=True)


class LoopState:
    """Manages state for iterative AI loops"""
    
    def __init__(self, loop_id: str, prompt: str, completion_promise: str, max_iterations: int = 20):
        self.loop_id = loop_id
        self.prompt = prompt
        self.completion_promise = completion_promise
        self.max_iterations = max_iterations
        self.current_iteration = 0
        self.context: List[str] = []
        self.files_modified: List[str] = []
        self.git_commits: List[str] = []
        self.start_time = datetime.now().isoformat()
        self.state_file = os.path.join(LOOP_STATE_DIR, f"{loop_id}.json")
        self.log_file = os.path.join(LOOP_LOG_DIR, f"{loop_id}.txt")
        self.completed = False
        self.completion_reason = ""
        
    def save(self) -> None:
        """Save loop state to file"""
        state_data = {
            "loop_id": self.loop_id,
            "prompt": self.prompt,
            "completion_promise": self.completion_promise,
            "max_iterations": self.max_iterations,
            "current_iteration": self.current_iteration,
            "context": self.context,
            "files_modified": self.files_modified,
            "git_commits": self.git_commits,
            "start_time": self.start_time,
            "completed": self.completed,
            "completion_reason": self.completion_reason,
        }
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save loop state: {e}")
    
    @classmethod
    def load(cls, loop_id: str) -> Optional['LoopState']:
        """Load loop state from file"""
        state_file = os.path.join(LOOP_STATE_DIR, f"{loop_id}.json")
        if not os.path.exists(state_file):
            return None
        
        try:
            with open(state_file, 'r') as f:
                state_data = json.load(f)
            
            loop = cls(
                state_data["loop_id"],
                state_data["prompt"],
                state_data["completion_promise"],
                state_data.get("max_iterations", 20)
            )
            loop.current_iteration = state_data.get("current_iteration", 0)
            loop.context = state_data.get("context", [])
            loop.files_modified = state_data.get("files_modified", [])
            loop.git_commits = state_data.get("git_commits", [])
            loop.start_time = state_data.get("start_time", datetime.now().isoformat())
            loop.completed = state_data.get("completed", False)
            loop.completion_reason = state_data.get("completion_reason", "")
            return loop
        except Exception as e:
            logger.error(f"Failed to load loop state: {e}")
            return None
    
    def add_iteration(self, response_text: str, executed_output: str = "") -> None:
        """Add iteration context"""
        iteration_data = f"Iteration {self.current_iteration}:\n{response_text}"
        if executed_output:
            iteration_data += f"\nExecution output:\n{executed_output}"
        self.context.append(iteration_data)
        self.current_iteration += 1
        self.save()
        
        # Log iteration
        self._log_iteration(iteration_data)
    
    def _log_iteration(self, iteration_data: str) -> None:
        """Log iteration to file"""
        try:
            with open(self.log_file, 'a') as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"{iteration_data}\n")
        except Exception as e:
            logger.error(f"Failed to log iteration: {e}")
    
    def check_completion(self, response_text: str) -> bool:
        """Check if completion promise is found in response"""
        # Use case-insensitive search
        pattern = re.escape(self.completion_promise)
        if re.search(pattern, response_text, re.IGNORECASE):
            self.completed = True
            self.completion_reason = f"Found completion promise: {self.completion_promise}"
            self.save()
            return True
        return False
    
    def get_context_string(self) -> str:
        """Build context string from previous iterations"""
        if not self.context:
            return ""
        
        # Summarize context if too long (keep last 5 iterations for performance)
        recent_context = self.context[-5:] if len(self.context) > 5 else self.context
        return "\n\n".join(recent_context)
    
    def build_prompt(self) -> str:
        """Build full prompt with context"""
        base_prompt = self.prompt
        context = self.get_context_string()
        
        # Add tool usage instructions for first iteration
        tool_instructions = ""
        if self.current_iteration == 0:
            tool_instructions = "\n\nCRITICAL: You MUST use tools in XML format to interact with files:\n\n<tool name=\"LS\"><param name=\"path\">.</param></tool>\n<tool name=\"View\"><param name=\"path\">filename.py</param></tool>\n<tool name=\"Bash\"><param name=\"command\">ls -la</param></tool>\n\nIf you cannot use XML format, describe tools clearly like:\n- \"Tool: LS\" or \"Use LS tool to list files\"\n- \"Tool: View file=main.py\" or \"Read the file main.py\"\n- \"Tool: Bash command='python test.py'\" or \"Run: python test.py\"\n\nStart by listing files, then read and refactor them."
        
        if context:
            return f"{base_prompt}{tool_instructions}\n\nPrevious iterations:\n{context}\n\nContinue working on this task. Output '{self.completion_promise}' when complete."
        else:
            return f"{base_prompt}{tool_instructions}\n\nOutput '{self.completion_promise}' when complete."
    
    def cleanup(self) -> None:
        """Clean up loop state files (optional, for completed loops)"""
        try:
            if os.path.exists(self.state_file):
                # Archive instead of delete for safety
                archive_file = self.state_file.replace('.json', '_completed.json')
                os.rename(self.state_file, archive_file)
        except Exception as e:
            logger.error(f"Failed to cleanup loop state: {e}")


def generate_loop_id() -> str:
    """Generate unique loop ID"""
    return f"loop_{int(time.time())}_{os.getpid()}"


def check_for_active_loop() -> Optional[str]:
    """Check for active (non-completed) loops"""
    if not os.path.exists(LOOP_STATE_DIR):
        return None
    
    try:
        for state_file in Path(LOOP_STATE_DIR).glob("loop_*.json"):
            if state_file.name.endswith("_completed.json"):
                continue
            
            try:
                with open(state_file, 'r') as f:
                    state_data = json.load(f)
                    if not state_data.get("completed", False):
                        return state_data.get("loop_id")
            except Exception:
                continue
    except Exception as e:
        logger.error(f"Error checking for active loops: {e}")
    
    return None


def cancel_active_loop(loop_id: Optional[str] = None) -> bool:
    """Cancel an active loop"""
    if loop_id is None:
        loop_id = check_for_active_loop()
    
    if loop_id is None:
        return False
    
    loop = LoopState.load(loop_id)
    if loop:
        loop.completed = True
        loop.completion_reason = "Cancelled by user"
        loop.save()
        return True
    return False


def run_eleven_loop(
    loop_id: str,
    prompt: str,
    completion_promise: str,
    max_iterations: int,
    api_key: str,
    config: Dict[str, Any],
    history: List[Dict[str, str]],
    args: Any = None
) -> str:
    """Run the iterative loop
    
    Args:
        loop_id: Unique identifier for the loop
        prompt: Initial task prompt
        completion_promise: Phrase to detect completion
        max_iterations: Maximum number of iterations
        api_key: API key for calls
        config: Configuration dict
        history: Conversation history
        args: Command line arguments (for tool execution)
    
    Returns:
        Final result message
    """
    try:
        from grok_agent import call_grok_api, extract_tools, get_env_context, get_system_prompt
        from main_helpers import execute_tool_safely
    except ImportError as e:
        return f"Error: Required modules not available: {e}"
    
    loop = LoopState(loop_id, prompt, completion_promise, max_iterations)
    loop.save()
    
    # Keep using orchestrator - it works, we'll parse natural language tool requests
    # The natural language parser handles conversational tool descriptions
    loop_config = config.copy()
    
    executed_outputs = []
    
    try:
        while loop.current_iteration < loop.max_iterations:
            if loop.completed:
                break
            
            # Build prompt with context
            full_prompt = loop.build_prompt()
            
            # Update system prompt with current context
            cwd, git_status, dir_tree = get_env_context()
            system_prompt = get_system_prompt(cwd, git_status, dir_tree)
            
            # Build messages
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(history[-10:] if len(history) > 10 else history)  # Include recent history
            messages.append({"role": "user", "content": full_prompt})
            
            # Call API
            print(f"\n{'-'*60}")
            print(f"Iteration {loop.current_iteration + 1}/{loop.max_iterations}")
            print(f"{'-'*60}\n")
            
            full_response = ""
            try:
                for chunk in call_grok_api(api_key, messages, config['model'], config['temperature'], config['max_tokens'], stream=True, config=loop_config):
                    content = chunk.get('choices', [{}])[0].get('delta', {}).get('content', '')
                    if content:
                        print(content, end='', flush=True)
                        full_response += content
                print()  # Newline after streaming
            except Exception as e:
                error_msg = f"API error: {e}"
                print(f"Error: {error_msg}")
                loop.add_iteration(f"Error: {error_msg}")
                break
            
            # Check for completion
            if loop.check_completion(full_response):
                print(f"\n✓ Completion promise '{completion_promise}' found!")
                loop.add_iteration(full_response)
                return f"Loop completed after {loop.current_iteration} iterations: {loop.completion_reason}"
            
            # Extract and execute tools
            executed_output = ""
            tool_calls = extract_tools(full_response)
            
            # Fallback: if no XML tools found, try natural language parsing
            if not tool_calls:
                tool_calls = extract_tools_from_natural_language(full_response)
                if tool_calls:
                    logger.debug(f"Extracted {len(tool_calls)} tools from natural language response")
            
            for tool_name, params_list in tool_calls:
                params = {p[0]: p[1] for p in params_list}
                if execute_tool_safely and args:
                    try:
                        exit_code, stdout, stderr = execute_tool_safely(tool_name, params, args, history)
                        if exit_code is not None and (stdout or stderr):
                            executed_output += f"\n[{tool_name}] Exit code: {exit_code}\n{stdout if stdout else stderr}"
                            executed_outputs.append(executed_output)
                    except Exception as e:
                        logger.error(f"Error executing tool {tool_name}: {e}")
                        executed_output += f"\n[{tool_name}] Error: {str(e)}"
            
            # Add iteration
            loop.add_iteration(full_response, executed_output)
            
            # Add to history for next iteration
            history.append({"role": "user", "content": full_prompt})
            history.append({"role": "assistant", "content": full_response})
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
        
        # Max iterations reached
        if not loop.completed:
            loop.completed = True
            loop.completion_reason = f"Max iterations ({max_iterations}) reached"
            loop.save()
            return f"Loop stopped after {loop.current_iteration} iterations (max reached). Partial output saved."
    
    except KeyboardInterrupt:
        loop.completed = True
        loop.completion_reason = "Interrupted by user"
        loop.save()
        return f"Loop interrupted after {loop.current_iteration} iterations"
    except Exception as e:
        loop.completed = True
        loop.completion_reason = f"Error: {str(e)}"
        loop.save()
        return f"Loop error: {str(e)}"
    
    return f"Loop completed: {loop.completion_reason}"
