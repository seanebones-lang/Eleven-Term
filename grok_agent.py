#!/usr/bin/env python3
"""
NextEleven Terminal Agent - eleven-powered, reverse-engineered from Claude Code
Agentic coding assistant with interactive mode, tool calling, hooks, and memory
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import httpx
import getpass
import hashlib
import random
import time
import fcntl
from datetime import datetime
from pathlib import Path
from functools import lru_cache
from typing import Optional, List, Dict, Any, Tuple, Iterator
from collections import OrderedDict
import asyncio
import threading

# Try to import disk cache (optional)
try:
    from cache_utils import get_disk_cache, DiskCache
    DISK_CACHE_AVAILABLE = True
except ImportError:
    DISK_CACHE_AVAILABLE = False
    DiskCache = None  # type: ignore

# Try to import plugin system (optional)
try:
    from plugin_system import get_tool as plugin_get_tool, execute_tool as plugin_execute_tool, load_plugins_from_directory, list_tools as plugin_list_tools
    PLUGIN_SYSTEM_AVAILABLE = True
except ImportError:
    PLUGIN_SYSTEM_AVAILABLE = False
    plugin_get_tool = None  # type: ignore
    plugin_execute_tool = None  # type: ignore
    load_plugins_from_directory = None  # type: ignore

# Try to import validation utils (optional)
try:
    from validation_utils import validate_tool_params, validate_command, validate_file_path
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False

# Try to import local LLM (optional)
try:
    from local_llm import check_ollama_available, call_ollama_api
    LOCAL_LLM_AVAILABLE = True
except ImportError:
    LOCAL_LLM_AVAILABLE = False
    check_ollama_available = None  # type: ignore
    call_ollama_api = None  # type: ignore

# Try to import agent chaining (optional)
try:
    from agent_chaining import chain_agents, AgentChain
    AGENT_CHAINING_AVAILABLE = True
except ImportError:
    AGENT_CHAINING_AVAILABLE = False

# Try to import multi-modal utils (optional)
try:
    from multimodal_utils import create_multimodal_messages, encode_image_to_base64
    MULTIMODAL_AVAILABLE = True
except ImportError:
    MULTIMODAL_AVAILABLE = False

# Try to import main helpers (optional)
try:
    from main_helpers import (
        handle_list_agents, handle_slash_commands, execute_tool_safely,
        compact_history_if_needed, initialize_interactive_session, run_interactive_loop
    )
    MAIN_HELPERS_AVAILABLE = True
except ImportError:
    MAIN_HELPERS_AVAILABLE = False

# Configure logging
_log_dir = os.path.expanduser('~/.grok_terminal')
os.makedirs(_log_dir, exist_ok=True)
_log_file = os.path.join(_log_dir, 'grok.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(_log_file),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# Try to import termcolor, fallback to ANSI codes if not available
try:
    from termcolor import colored
except ImportError:
    # Fallback colored function
    class Colors:
        RESET = '\033[0m'
        RED = '\033[31m'
        GREEN = '\033[32m'
        YELLOW = '\033[33m'
        BLUE = '\033[34m'
        MAGENTA = '\033[35m'
        CYAN = '\033[36m'
    
    def colored(text, color=None, attrs=None):
        color_map = {
            'red': Colors.RED,
            'green': Colors.GREEN,
            'yellow': Colors.YELLOW,
            'blue': Colors.BLUE,
            'magenta': Colors.MAGENTA,
            'cyan': Colors.CYAN,
        }
        return f"{color_map.get(color, '')}{text}{Colors.RESET}"

# Try to import security utilities (preserve existing security)
try:
    from security_utils import sanitize_input, sanitize_command, SecurityError, execute_command_safely
except ImportError:
    def sanitize_input(text: str, max_length: int = 10000) -> str:
        if not isinstance(text, str) or len(text) > max_length:
            raise ValueError("Invalid input")
        return text.replace('\x00', '').strip()
    
    def sanitize_command(cmd: str) -> str:
        return sanitize_input(cmd)
    
    class SecurityError(Exception):
        pass
    
    def execute_command_safely(cmd: str, allow_force: bool = False, timeout: int = 60):
        """Fallback safe execution"""
        import shlex
        try:
            args = shlex.split(cmd)
            return subprocess.run(args, shell=False, capture_output=True, text=True, timeout=timeout)
        except ValueError:
            return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)

# Production constants
HISTORY_MESSAGE_LIMIT = 40  # Keep last 40 messages (20 user+assistant pairs)
DIR_TREE_MAX_LENGTH = 500  # Maximum directory tree length
DEFAULT_TIMEOUT = 60  # Default command timeout in seconds
RETRY_JITTER_PERCENT = 0.3  # Jitter percentage for retry backoff
MAX_REQUEST_SIZE = 100 * 1024  # 100KB max request size
MAX_RESPONSE_SIZE = 10 * 1024 * 1024  # 10MB max response size
HISTORY_COMPACT_THRESHOLD = 20  # Compact history when > 20 messages
CACHE_DEFAULT_TTL = 300  # 5 minutes default cache TTL
CACHE_DEFAULT_SIZE = 100  # Default cache size

# Config defaults (Claude-like)
DEFAULT_CONFIG = {
    "model": "grok-4.1-fast",  # Latest model as of January 2026
    "api_endpoint": "https://grokcode.vercel.app/api/chat",  # Default to Grok-Code orchestrator (all requests go through orchestrator)
    "temperature": 0.1,
    "max_tokens": 2048,
    "auto_log": True,
    "dangerous_commands_require_flag": True,
    "history_file": "~/.grok_terminal_history.json",
    "todos_file": "~/.grok_terminal/todos.json",
    "hooks_dir": "~/.grok_terminal/hooks/",
    "cache_enabled": True,
    "cache_size": CACHE_DEFAULT_SIZE,
    "cache_ttl": CACHE_DEFAULT_TTL,
    "max_retries": 3,
    "retry_base_delay": 1.0,
    "retry_max_delay": 60.0,
    "health_check_enabled": True,
    # Specialized agent mapping for Grok-Code agents
    "agent_endpoints": {
        # Main endpoint supports all agents via /api/chat with mode parameter
        "grokcode_endpoint": "https://grokcode.vercel.app/api/chat",
    },
    # Specialized Agents from Grok-Code repository (https://github.com/seanebones-lang/Grok-Code)
    "specialized_agents": {
        "security": {
            "name": "Security Agent",
            "emoji": "🔒",
            "mode": "agent",
            "agent": "security",
            "description": "Scans for vulnerabilities, security issues, and compliance violations"
        },
        "performance": {
            "name": "Performance Agent",
            "emoji": "⚡",
            "mode": "agent",
            "agent": "performance",
            "description": "Analyzes and optimizes code performance, bottlenecks, and resource usage"
        },
        "testing": {
            "name": "Testing Agent",
            "emoji": "🧪",
            "mode": "agent",
            "agent": "testing",
            "description": "Generates comprehensive test suites, coverage reports, and test strategies"
        },
        "documentation": {
            "name": "Documentation Agent",
            "emoji": "📚",
            "mode": "agent",
            "agent": "documentation",
            "description": "Generates comprehensive documentation, README files, and API docs"
        },
        "migration": {
            "name": "Migration Agent",
            "emoji": "🔄",
            "mode": "agent",
            "agent": "migration",
            "description": "Handles framework/library migrations and version upgrades"
        },
        "dependency": {
            "name": "Dependency Agent",
            "emoji": "📦",
            "mode": "agent",
            "agent": "dependency",
            "description": "Manages dependencies, updates, and resolves conflicts"
        },
        "codeReview": {
            "name": "Code Review Agent",
            "emoji": "🔍",
            "mode": "agent",
            "agent": "codeReview",
            "description": "Performs deep code reviews with best practices and quality checks"
        },
        "bugHunter": {
            "name": "Bug Hunter Agent",
            "emoji": "🐛",
            "mode": "agent",
            "agent": "bugHunter",
            "description": "Specialized bug detection and debugging with root cause analysis"
        },
        "debugging": {
            "name": "Debugging Agent",
            "emoji": "🐛",
            "mode": "agent",
            "agent": "debugging",
            "description": "Expert in debugging techniques, error analysis, log analysis, and troubleshooting complex issues"
        },
        "code-review": {
            "name": "Code Review Agent",
            "emoji": "👀",
            "mode": "agent",
            "agent": "code-review",
            "description": "Expert in code review, identifying bugs, suggesting improvements, and ensuring code quality standards"
        },
        "optimization": {
            "name": "Optimization Agent",
            "emoji": "🎯",
            "mode": "agent",
            "agent": "optimization",
            "description": "Code optimization, refactoring, and efficiency improvements"
        },
        "accessibility": {
            "name": "Accessibility Agent",
            "emoji": "♿",
            "mode": "agent",
            "agent": "accessibility",
            "description": "Ensures code meets WCAG standards and accessibility best practices"
        },
        "uiux": {
            "name": "UI/UX Agent",
            "emoji": "🎨",
            "mode": "agent",
            "agent": "uiux",
            "description": "Design systems, components, styling, and user experience"
        },
        "backend": {
            "name": "Backend Agent",
            "emoji": "⚙️",
            "mode": "agent",
            "agent": "backend",
            "description": "Expert in backend development, server architecture, APIs, microservices, and server-side technologies"
        },
        "frontend": {
            "name": "Frontend Agent",
            "emoji": "💻",
            "mode": "agent",
            "agent": "frontend",
            "description": "Expert in frontend development, modern frameworks, responsive design, and client-side technologies"
        },
        "devops": {
            "name": "DevOps Agent",
            "emoji": "🚀",
            "mode": "agent",
            "agent": "devops",
            "description": "CI/CD pipelines, Docker, Kubernetes, infrastructure as code"
        },
        "database": {
            "name": "Database Agent",
            "emoji": "🗄️",
            "mode": "agent",
            "agent": "database",
            "description": "Database design, queries, migrations, and optimization"
        },
        "api": {
            "name": "API Design Agent",
            "emoji": "🔌",
            "mode": "agent",
            "agent": "api",
            "description": "REST API, GraphQL, WebSocket, and API design patterns"
        },
        "cloud": {
            "name": "Cloud Agent",
            "emoji": "☁️",
            "mode": "agent",
            "agent": "cloud",
            "description": "Expert in cloud platforms (AWS, GCP, Azure), cloud architecture, serverless, and cloud-native development"
        },
        "mobile": {
            "name": "Mobile App Agent",
            "emoji": "📱",
            "mode": "agent",
            "agent": "mobile",
            "description": "Expert in React Native, Flutter, iOS & Android mobile development"
        },
        "aiml": {
            "name": "AI/ML Agent",
            "emoji": "🤖",
            "mode": "agent",
            "agent": "aiml",
            "description": "Machine learning integration, LLMs, embeddings, and AI pipelines"
        },
        "blockchain": {
            "name": "Blockchain Agent",
            "emoji": "⛓️",
            "mode": "agent",
            "agent": "blockchain",
            "description": "Expert in blockchain technology, smart contracts, cryptocurrency, and decentralized applications"
        },
        "orchestrator": {
            "name": "Orchestrator Agent",
            "emoji": "🎼",
            "mode": "orchestrate",
            "agent": "orchestrator",
            "description": "Coordinates and delegates tasks to multiple specialized agents"
        },
        "swarm": {
            "name": "Agent Swarm",
            "emoji": "🐝",
            "mode": "agent",
            "agent": "swarm",
            "description": "Runs multiple agents in parallel for comprehensive analysis"
        },
        "data": {
            "name": "Data Engineering Agent",
            "emoji": "📊",
            "mode": "agent",
            "agent": "data",
            "description": "Data pipelines, ETL, analytics, and data transformation"
        },
        "fullstack": {
            "name": "Full Stack Agent",
            "emoji": "🏗️",
            "mode": "agent",
            "agent": "fullstack",
            "description": "End-to-end feature development across frontend and backend"
        },
        "xcode": {
            "name": "Xcode Expert Agent",
            "emoji": "📱",
            "mode": "agent",
            "agent": "xcode",
            "description": "25-year expert in Xcode, Swift, iOS, Apple App Store rules, troubleshooting, latest tech (Jan 2026), best build practices, iOS UI/UX"
        },
        "android": {
            "name": "Android Expert Agent",
            "emoji": "🤖",
            "mode": "agent",
            "agent": "android",
            "description": "25-year expert in Android Studio, Kotlin, Java, Android, Google Play Store rules, troubleshooting, latest tech (Jan 2026), best build practices, Android UI/UX"
        },
        "refactoring": {
            "name": "Refactoring Agent",
            "emoji": "♻️",
            "mode": "agent",
            "agent": "refactoring",
            "description": "Expert in code refactoring, improving code quality, reducing technical debt, and maintaining clean code architecture"
        },
    }
}

# Global HTTP client for connection pooling
_http_client: Optional[httpx.Client] = None
_http_async_client: Optional[httpx.AsyncClient] = None

# Response cache (in-memory, LRU with semantic hash based keys)
_response_cache: OrderedDict[str, Tuple[float, Any]] = OrderedDict()  # hash -> (timestamp, response)
_cache_stats: Dict[str, int] = {"hits": 0, "misses": 0, "evictions": 0}  # Cache statistics
_disk_cache: Optional[DiskCache] = None  # Disk cache instance (optional)

# Request deduplication (track in-flight requests)
_in_flight_requests: Dict[str, Any] = {}
_in_flight_lock = threading.Lock()  # Lock for thread-safe access

# Dangerous patterns (expanded from Claude's Bash security)
DANGEROUS_PATTERNS = [
    r'rm\s+-rf', r'sudo\s+', r'kill\s+-9', r'mkfs\b', r'dd\s+if=', r'chmod\s+777',
    r'>\s*/dev/', r'\bformat\b', r'\bfdisk\b', r'rm\s+.*', r'del\s+.*'
]

# API endpoint (default to Grok-Code orchestrator, can override)
API_ENDPOINT = "https://grokcode.vercel.app/api/chat"

# System prompt (reverse-engineered from Claude: inject env, tools, reminders)
def get_system_prompt(cwd: str, git_status: str, dir_tree: str) -> str:
    # Detect project types for context (orchestrator will use this to assign agents)
    project_info = ""
    project_type = None
    try:
        from xcode_utils import find_xcode_project
        xcode_project = find_xcode_project(cwd)
        if xcode_project:
            project_info = f"\nXcode project detected: {xcode_project}"
            project_type = "xcode"
    except ImportError:
        pass
    
    if not project_type:
        try:
            from android_utils import find_android_project
            android_project = find_android_project(cwd)
            if android_project:
                project_info = f"\nAndroid project detected: {android_project}"
                project_type = "android"
        except ImportError:
            pass
    
    # All tools available to all agents (as of Jan 10, 2026)
    tools_list = (
        "Bash (execute shell), View (read file), Edit (edit file), Write (write file), "
        "LS (list dir), Glob (pattern search), Grep (search text), "
        "XcodeProjectInfo (Xcode project info), XcodeListFiles (list Xcode files), "
        "XcodeReadFile (read Xcode source), XcodeWriteFile (write Xcode source), "
        "XcodeBuild (build Xcode project), XcodeOpen (open in Xcode), "
        "AndroidProjectInfo (Android project info), AndroidListFiles (list Android files), "
        "AndroidReadFile (read Android source), AndroidWriteFile (write Android source), "
        "AndroidBuild (build Android project), AndroidOpen (open in Android Studio), "
        "AndroidStudioInfo (Android Studio/SDK info), AndroidListEmulators (list emulators), "
        "AndroidStartEmulator (start emulator), AndroidListDevices (list connected devices), "
        "AndroidSDKManager (SDK Manager info), "
        "MySQLQuery (execute MySQL query), PostgreSQLQuery (execute PostgreSQL query), "
        "MongoDBQuery (execute MongoDB query), RedisCommand (execute Redis command), "
        "HTTPieRequest (HTTP request via HTTPie), CurlRequest (HTTP request via curl)"
    )
    
    return f"""You are eleven Terminal Agent, a helpful coding assistant in the terminal. 
Current dir: {cwd}
Git status: {git_status}
Dir structure: {dir_tree}{project_info}
All tools available (Jan 10, 2026): {tools_list}
Use tool calling format: <tool name="ToolName"><param name="param1">value</param></tool>
Be concise for CLI. Maintain todos if mentioned. Use appropriate tools based on project type."""

# Lightweight topic prompt (emulates Claude's check-new-topic)
TOPIC_PROMPT = "Analyze if this starts a new topic: {input}. Return JSON: {{\"isNewTopic\": bool, \"title\": str}}"

# Context compaction prompt (emulates Claude's compact)
COMPACT_PROMPT = "Summarize this conversation history concisely: {history}"

# Tools implementation (Python equivalents of Claude's tools)
def tool_bash(params: Dict[str, Any], allow_force: bool = False) -> Tuple[int, str, str]:
    """Execute bash command safely"""
    command = params.get('command', '')
    if not command:
        return 1, "", "No command provided"
    
    try:
        result = execute_command_safely(command, allow_force=allow_force, timeout=60, auto_sudo=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def tool_view(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """View file contents"""
    path = params.get('path', '')
    if not path:
        return 1, "", "No path provided"
    
    try:
        expanded_path = os.path.expanduser(path)
        if not os.path.exists(expanded_path):
            return 1, "", f"File not found: {path}"
        
        with open(expanded_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return 0, content, ""
    except Exception as e:
        return 1, "", str(e)

def tool_edit(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Edit file using vim"""
    path = params.get('path', '')
    if not path:
        return 1, "", "No path provided"
    
    try:
        expanded_path = os.path.expanduser(path)
        # Use vim to edit (blocking)
        result = subprocess.run(['vim', expanded_path], timeout=300)
        return result.returncode, "", ""
    except subprocess.TimeoutExpired:
        return 1, "", "Edit timeout"
    except Exception as e:
        return 1, "", str(e)

def tool_write(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Write content to file"""
    path = params.get('path', '')
    content = params.get('content', '')
    
    if not path:
        return 1, "", "No path provided"
    
    try:
        expanded_path = os.path.expanduser(path)
        os.makedirs(os.path.dirname(expanded_path) if os.path.dirname(expanded_path) else '.', exist_ok=True)
        
        with open(expanded_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return 0, f"Written to {path}", ""
    except Exception as e:
        return 1, "", str(e)

def tool_ls(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """List directory contents"""
    dir_path = params.get('dir', '.')
    
    try:
        expanded_path = os.path.expanduser(dir_path)
        if not os.path.exists(expanded_path):
            return 1, "", f"Directory not found: {dir_path}"
        
        items = os.listdir(expanded_path)
        return 0, '\n'.join(items), ""
    except Exception as e:
        return 1, "", str(e)

def tool_glob(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Glob pattern search"""
    pattern = params.get('pattern', '')
    if not pattern:
        return 1, "", "No pattern provided"
    
    try:
        from glob import glob
        matches = glob(pattern, recursive=True)
        return 0, '\n'.join(matches), ""
    except Exception as e:
        return 1, "", str(e)

def tool_grep(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Grep search in files"""
    query = params.get('query', '')
    dir_path = params.get('dir', '.')
    
    if not query:
        return 1, "", "No query provided"
    
    try:
        expanded_path = os.path.expanduser(dir_path)
        result = subprocess.run(
            ['grep', '-r', '-n', query, expanded_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Grep timeout"
    except Exception as e:
        return 1, "", str(e)

def tool_xcode_project_info(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Get information about Xcode project"""
    try:
        from xcode_utils import find_xcode_project, read_xcode_project_info
        project_path = params.get('path', '.')
        
        if project_path == '.' or not project_path:
            found_project = find_xcode_project('.')
            if not found_project:
                return 1, "", "No Xcode project found in current directory"
            project_path = found_project
        
        info = read_xcode_project_info(project_path)
        
        if info.get('error'):
            return 1, "", info['error']
        
        output = json.dumps(info, indent=2)
        return 0, output, ""
    except ImportError:
        return 1, "", "xcode_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_xcode_list_files(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """List files in Xcode project"""
    try:
        from xcode_utils import find_xcode_project, list_xcode_files
        project_path = params.get('path', '.')
        file_type = params.get('file_type', 'all')  # 'swift', 'objc', 'all'
        
        if project_path == '.' or not project_path:
            found_project = find_xcode_project('.')
            if not found_project:
                return 1, "", "No Xcode project found in current directory"
            project_path = found_project
        
        files = list_xcode_files(project_path, file_type)
        output = '\n'.join(files) if files else "No files found"
        return 0, output, ""
    except ImportError:
        return 1, "", "xcode_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_xcode_read_file(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Read Xcode source file (Swift, Objective-C, etc.)"""
    try:
        from xcode_utils import read_xcode_file
        file_path = params.get('path', '')
        if not file_path:
            return 1, "", "No path provided"
        
        return read_xcode_file(file_path)
    except ImportError:
        return 1, "", "xcode_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_xcode_write_file(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Write content to Xcode source file"""
    try:
        from xcode_utils import write_xcode_file
        file_path = params.get('path', '')
        content = params.get('content', '')
        
        if not file_path:
            return 1, "", "No path provided"
        
        return write_xcode_file(file_path, content)
    except ImportError:
        return 1, "", "xcode_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_xcode_build(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Build Xcode project"""
    try:
        from xcode_utils import find_xcode_project, build_xcode_project
        project_path = params.get('path', '.')
        scheme = params.get('scheme', None)
        configuration = params.get('configuration', 'Debug')
        
        if project_path == '.' or not project_path:
            found_project = find_xcode_project('.')
            if not found_project:
                return 1, "", "No Xcode project found in current directory"
            project_path = found_project
        
        return build_xcode_project(project_path, scheme, configuration)
    except ImportError:
        return 1, "", "xcode_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_xcode_open(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Open Xcode project in Xcode app"""
    try:
        from xcode_utils import find_xcode_project, open_xcode_project
        project_path = params.get('path', '.')
        
        if project_path == '.' or not project_path:
            found_project = find_xcode_project('.')
            if not found_project:
                return 1, "", "No Xcode project found in current directory"
            project_path = found_project
        
        return open_xcode_project(project_path)
    except ImportError:
        return 1, "", "xcode_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_android_project_info(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Get information about Android Studio project"""
    try:
        from android_utils import find_android_project, read_android_project_info
        project_path = params.get('path', '.')
        
        if project_path == '.' or not project_path:
            found_project = find_android_project('.')
            if not found_project:
                return 1, "", "No Android project found in current directory"
            project_path = found_project
        
        info = read_android_project_info(project_path)
        
        if info.get('error'):
            return 1, "", info['error']
        
        output = json.dumps(info, indent=2)
        return 0, output, ""
    except ImportError:
        return 1, "", "android_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_android_list_files(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """List files in Android Studio project"""
    try:
        from android_utils import find_android_project, list_android_files
        project_path = params.get('path', '.')
        file_type = params.get('file_type', 'all')  # 'kotlin', 'java', 'xml', 'all'
        
        if project_path == '.' or not project_path:
            found_project = find_android_project('.')
            if not found_project:
                return 1, "", "No Android project found in current directory"
            project_path = found_project
        
        files = list_android_files(project_path, file_type)
        output = '\n'.join(files) if files else "No files found"
        return 0, output, ""
    except ImportError:
        return 1, "", "android_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_android_read_file(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Read Android source file (Kotlin, Java, XML, etc.)"""
    try:
        from android_utils import read_android_file
        file_path = params.get('path', '')
        if not file_path:
            return 1, "", "No path provided"
        
        return read_android_file(file_path)
    except ImportError:
        return 1, "", "android_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_android_write_file(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Write content to Android source file"""
    try:
        from android_utils import write_android_file
        file_path = params.get('path', '')
        content = params.get('content', '')
        
        if not file_path:
            return 1, "", "No path provided"
        
        return write_android_file(file_path, content)
    except ImportError:
        return 1, "", "android_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_android_build(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Build Android Studio project"""
    try:
        from android_utils import find_android_project, build_android_project
        project_path = params.get('path', '.')
        variant = params.get('variant', None)
        task = params.get('task', 'assembleDebug')  # assembleDebug, assembleRelease, etc.
        
        if project_path == '.' or not project_path:
            found_project = find_android_project('.')
            if not found_project:
                return 1, "", "No Android project found in current directory"
            project_path = found_project
        
        return build_android_project(project_path, variant, task)
    except ImportError:
        return 1, "", "android_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_android_open(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Open Android Studio project in Android Studio app"""
    try:
        from android_utils import find_android_project, open_android_project
        project_path = params.get('path', '.')
        
        if project_path == '.' or not project_path:
            found_project = find_android_project('.')
            if not found_project:
                return 1, "", "No Android project found in current directory"
            project_path = found_project
        
        return open_android_project(project_path)
    except ImportError:
        return 1, "", "android_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_android_studio_info(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Get Android Studio and SDK information"""
    try:
        from android_utils import get_android_studio_info
        import json
        info = get_android_studio_info()
        return 0, json.dumps(info, indent=2), ""
    except ImportError:
        return 1, "", "android_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_android_list_emulators(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """List available Android emulators"""
    try:
        from android_utils import list_android_emulators
        code, emulators, error = list_android_emulators()
        if code == 0:
            output = '\n'.join(emulators) if emulators else "No emulators found"
            return 0, output, error
        return code, "", error
    except ImportError:
        return 1, "", "android_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_android_start_emulator(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Start Android emulator"""
    try:
        from android_utils import start_android_emulator
        avd_name = params.get('avd_name', '')
        background = params.get('background', True)
        
        if not avd_name:
            return 1, "", "No AVD name provided"
        
        return start_android_emulator(avd_name, background)
    except ImportError:
        return 1, "", "android_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_android_list_devices(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """List connected Android devices (via ADB)"""
    try:
        from android_utils import list_android_devices
        import json
        code, devices, error = list_android_devices()
        if code == 0:
            output = json.dumps(devices, indent=2) if devices else "No devices connected"
            return 0, output, error
        return code, "", error
    except ImportError:
        return 1, "", "android_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_android_sdk_manager(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Open Android SDK Manager or get SDK info"""
    try:
        from android_utils import open_android_sdk_manager
        return open_android_sdk_manager()
    except ImportError:
        return 1, "", "android_utils module not available"
    except Exception as e:
        return 1, "", str(e)

# Database Tools
def tool_mysql_query(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Execute MySQL query"""
    try:
        from database_utils import execute_mysql_query
        host = params.get('host', 'localhost')
        user = params.get('user', 'root')
        database = params.get('database', '')
        query = params.get('query', '')
        password = params.get('password', None)
        
        if not database or not query:
            return 1, "", "database and query parameters required"
        
        return execute_mysql_query(host, user, database, query, password)
    except ImportError:
        return 1, "", "database_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_postgresql_query(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Execute PostgreSQL query"""
    try:
        from database_utils import execute_postgresql_query
        host = params.get('host', 'localhost')
        user = params.get('user', 'postgres')
        database = params.get('database', '')
        query = params.get('query', '')
        password = params.get('password', None)
        
        if not database or not query:
            return 1, "", "database and query parameters required"
        
        return execute_postgresql_query(host, user, database, query, password)
    except ImportError:
        return 1, "", "database_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_mongodb_query(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Execute MongoDB query"""
    try:
        from database_utils import execute_mongodb_query
        uri = params.get('uri', 'mongodb://localhost:27017')
        database = params.get('database', '')
        collection = params.get('collection', '')
        query = params.get('query', '')
        
        if not database or not collection or not query:
            return 1, "", "database, collection, and query parameters required"
        
        return execute_mongodb_query(uri, database, collection, query)
    except ImportError:
        return 1, "", "database_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_redis_command(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Execute Redis command"""
    try:
        from database_utils import execute_redis_command
        host = params.get('host', 'localhost')
        port = params.get('port', 6379)
        command = params.get('command', '')
        password = params.get('password', None)
        
        if not command:
            return 1, "", "command parameter required"
        
        return execute_redis_command(host, port, command, password)
    except ImportError:
        return 1, "", "database_utils module not available"
    except Exception as e:
        return 1, "", str(e)

# API Tools
def tool_httpie_request(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Execute HTTP request using HTTPie"""
    try:
        from api_utils import httpie_request
        method = params.get('method', 'GET')
        url = params.get('url', '')
        headers = params.get('headers', None)
        data = params.get('data', None)
        json_data = params.get('json', None)
        
        if not url:
            return 1, "", "url parameter required"
        
        return httpie_request(method, url, headers, data, json_data)
    except ImportError:
        return 1, "", "api_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_curl_request(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Execute HTTP request using curl (enhanced)"""
    try:
        from api_utils import curl_request
        method = params.get('method', 'GET')
        url = params.get('url', '')
        headers = params.get('headers', None)
        data = params.get('data', None)
        json_data = params.get('json', None)
        
        if not url:
            return 1, "", "url parameter required"
        
        return curl_request(method, url, headers, data, json_data)
    except ImportError:
        return 1, "", "api_utils module not available"
    except Exception as e:
        return 1, "", str(e)

# Security Scanning Tools
def tool_snyk_test(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Run Snyk security test"""
    try:
        from security_scanning_utils import snyk_test
        path = params.get('path', '.')
        severity = params.get('severity', 'low')
        return snyk_test(path, severity)
    except ImportError:
        return 1, "", "security_scanning_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_trivy_scan(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Scan with Trivy (container or filesystem)"""
    try:
        from security_scanning_utils import trivy_scan_image, trivy_scan_filesystem
        scan_type = params.get('type', 'filesystem')  # 'image' or 'filesystem'
        target = params.get('target', '.')
        severity = params.get('severity', 'UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL')
        
        if scan_type == 'image':
            return trivy_scan_image(target, severity)
        else:
            return trivy_scan_filesystem(target, severity)
    except ImportError:
        return 1, "", "security_scanning_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_semgrep_scan(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Run Semgrep security scan"""
    try:
        from security_scanning_utils import semgrep_scan
        path = params.get('path', '.')
        config = params.get('config', 'auto')
        return semgrep_scan(path, config)
    except ImportError:
        return 1, "", "security_scanning_utils module not available"
    except Exception as e:
        return 1, "", str(e)

# Performance Profiling Tools
def tool_py_spy_top(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Show top Python functions using py-spy"""
    try:
        from profiling_utils import py_spy_top
        pid = params.get('pid', None)
        duration = params.get('duration', 10)
        
        if not pid:
            return 1, "", "pid parameter required"
        
        return py_spy_top(pid, duration)
    except ImportError:
        return 1, "", "profiling_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_cprofile_analyze(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Analyze cProfile stats file"""
    try:
        from profiling_utils import analyze_profile_stats
        stats_file = params.get('stats_file', '')
        top_n = params.get('top_n', 20)
        
        if not stats_file:
            return 1, "", "stats_file parameter required"
        
        return analyze_profile_stats(stats_file, top_n)
    except ImportError:
        return 1, "", "profiling_utils module not available"
    except Exception as e:
        return 1, "", str(e)

# Load Testing Tools
def tool_k6_run(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Run k6 load test"""
    try:
        from load_testing_utils import k6_run, k6_simple_url
        script_path = params.get('script', None)
        url = params.get('url', None)
        duration = params.get('duration', '30s')
        vus = params.get('vus', 10)
        
        if script_path:
            return k6_run(script_path, duration, vus)
        elif url:
            return k6_simple_url(url, duration, vus)
        else:
            return 1, "", "script or url parameter required"
    except ImportError:
        return 1, "", "load_testing_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_wrk_benchmark(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Run wrk HTTP benchmark"""
    try:
        from load_testing_utils import wrk_benchmark
        url = params.get('url', '')
        threads = params.get('threads', 4)
        connections = params.get('connections', 10)
        duration = params.get('duration', '30s')
        
        if not url:
            return 1, "", "url parameter required"
        
        return wrk_benchmark(url, threads, connections, duration)
    except ImportError:
        return 1, "", "load_testing_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_ab_benchmark(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Run Apache Bench (ab) benchmark"""
    try:
        from load_testing_utils import ab_benchmark
        url = params.get('url', '')
        requests = params.get('requests', 1000)
        concurrency = params.get('concurrency', 10)
        
        if not url:
            return 1, "", "url parameter required"
        
        return ab_benchmark(url, requests, concurrency)
    except ImportError:
        return 1, "", "load_testing_utils module not available"
    except Exception as e:
        return 1, "", str(e)

# CI/CD Tools
def tool_gh_workflow_list(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """List GitHub Actions workflows"""
    try:
        from cicd_utils import gh_workflow_list
        repo = params.get('repo', None)
        return gh_workflow_list(repo)
    except ImportError:
        return 1, "", "cicd_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_gh_run_list(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """List GitHub Actions workflow runs"""
    try:
        from cicd_utils import gh_run_list
        repo = params.get('repo', None)
        limit = params.get('limit', 10)
        return gh_run_list(repo, limit)
    except ImportError:
        return 1, "", "cicd_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_gh_run_view(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """View GitHub Actions workflow run"""
    try:
        from cicd_utils import gh_run_view
        run_id = params.get('run_id', '')
        repo = params.get('repo', None)
        
        if not run_id:
            return 1, "", "run_id parameter required"
        
        return gh_run_view(run_id, repo)
    except ImportError:
        return 1, "", "cicd_utils module not available"
    except Exception as e:
        return 1, "", str(e)

# Database Migration Tools
def tool_alembic_current(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Show current Alembic migration revision"""
    try:
        from migration_utils import alembic_current
        directory = params.get('directory', '.')
        return alembic_current(directory)
    except ImportError:
        return 1, "", "migration_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_alembic_upgrade(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Upgrade database using Alembic"""
    try:
        from migration_utils import alembic_upgrade
        revision = params.get('revision', 'head')
        directory = params.get('directory', '.')
        return alembic_upgrade(revision, directory)
    except ImportError:
        return 1, "", "migration_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_dbmate_up(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Run dbmate migrations up"""
    try:
        from migration_utils import dbmate_up
        database_url = params.get('database_url', None)
        return dbmate_up(database_url)
    except ImportError:
        return 1, "", "migration_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_dbmate_status(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Show dbmate migration status"""
    try:
        from migration_utils import dbmate_status
        database_url = params.get('database_url', None)
        return dbmate_status(database_url)
    except ImportError:
        return 1, "", "migration_utils module not available"
    except Exception as e:
        return 1, "", str(e)

# Container Orchestration Tools
def tool_kubectl_get(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Get Kubernetes resources"""
    try:
        from orchestration_utils import kubectl_get
        resource = params.get('resource', '')
        namespace = params.get('namespace', None)
        output_format = params.get('output', 'json')
        
        if not resource:
            return 1, "", "resource parameter required"
        
        return kubectl_get(resource, namespace, output_format)
    except ImportError:
        return 1, "", "orchestration_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_helm_list(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """List Helm releases"""
    try:
        from orchestration_utils import helm_list
        namespace = params.get('namespace', None)
        return helm_list(namespace)
    except ImportError:
        return 1, "", "orchestration_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_docker_compose_up(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Start Docker Compose services"""
    try:
        from orchestration_utils import docker_compose_up
        compose_file = params.get('compose_file', None)
        services = params.get('services', None)
        detach = params.get('detach', True)
        return docker_compose_up(compose_file, services, detach)
    except ImportError:
        return 1, "", "orchestration_utils module not available"
    except Exception as e:
        return 1, "", str(e)

# Secrets Management Tools
def tool_vault_read(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Read secret from Vault"""
    try:
        from secrets_utils import vault_read
        path = params.get('path', '')
        field = params.get('field', None)
        
        if not path:
            return 1, "", "path parameter required"
        
        return vault_read(path, field)
    except ImportError:
        return 1, "", "secrets_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_sops_decrypt(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Decrypt file with SOPS"""
    try:
        from secrets_utils import sops_decrypt
        file_path = params.get('file', '')
        output_file = params.get('output', None)
        
        if not file_path:
            return 1, "", "file parameter required"
        
        return sops_decrypt(file_path, output_file)
    except ImportError:
        return 1, "", "secrets_utils module not available"
    except Exception as e:
        return 1, "", str(e)

# Tools registry
# Initialize plugin system if available
if PLUGIN_SYSTEM_AVAILABLE and load_plugins_from_directory:
    try:
        plugin_dir = os.path.expanduser('~/.grok_terminal/plugins')
        if os.path.exists(plugin_dir):
            load_plugins_from_directory(plugin_dir)
    except Exception as e:
        logger.debug(f"Could not load plugins: {e}")

TOOLS = {
    "Bash": tool_bash,
    "View": tool_view,
    "Edit": tool_edit,
    "Write": tool_write,
    "LS": tool_ls,
    "Glob": tool_glob,
    "Grep": tool_grep,
    "XcodeProjectInfo": tool_xcode_project_info,
    "XcodeListFiles": tool_xcode_list_files,
    "XcodeReadFile": tool_xcode_read_file,
    "XcodeWriteFile": tool_xcode_write_file,
    "XcodeBuild": tool_xcode_build,
    "XcodeOpen": tool_xcode_open,
    "AndroidProjectInfo": tool_android_project_info,
    "AndroidListFiles": tool_android_list_files,
    "AndroidReadFile": tool_android_read_file,
    "AndroidWriteFile": tool_android_write_file,
    "AndroidBuild": tool_android_build,
    "AndroidOpen": tool_android_open,
    "AndroidStudioInfo": tool_android_studio_info,
    "AndroidListEmulators": tool_android_list_emulators,
    "AndroidStartEmulator": tool_android_start_emulator,
    "AndroidListDevices": tool_android_list_devices,
    "AndroidSDKManager": tool_android_sdk_manager,
    # Database Tools
    "MySQLQuery": tool_mysql_query,
    "PostgreSQLQuery": tool_postgresql_query,
    "MongoDBQuery": tool_mongodb_query,
    "RedisCommand": tool_redis_command,
    # API Tools
    "HTTPieRequest": tool_httpie_request,
    "CurlRequest": tool_curl_request,
    # Security Scanning Tools
    "SnykTest": tool_snyk_test,
    "TrivyScan": tool_trivy_scan,
    "SemgrepScan": tool_semgrep_scan,
    # Performance Profiling Tools
    "PySpyTop": tool_py_spy_top,
    "CProfileAnalyze": tool_cprofile_analyze,
    # Load Testing Tools
    "K6Run": tool_k6_run,
    "WrkBenchmark": tool_wrk_benchmark,
    "ABBenchmark": tool_ab_benchmark,
    # CI/CD Tools
    "GHWorkflowList": tool_gh_workflow_list,
    "GHRunList": tool_gh_run_list,
    "GHRunView": tool_gh_run_view,
    # Database Migration Tools
    "AlembicCurrent": tool_alembic_current,
    "AlembicUpgrade": tool_alembic_upgrade,
    "DBMateUp": tool_dbmate_up,
    "DBMateStatus": tool_dbmate_status,
    # Container Orchestration Tools
    "KubectlGet": tool_kubectl_get,
    "HelmList": tool_helm_list,
    "DockerComposeUp": tool_docker_compose_up,
    # Secrets Management Tools
    "VaultRead": tool_vault_read,
    "SopsDecrypt": tool_sops_decrypt,
}

def get_api_key() -> Optional[str]:
    """Retrieve API key from macOS Keychain"""
    try:
        result = subprocess.run(
            ['security', 'find-generic-password', '-s', 'grok-terminal', '-a', 'xai-api-key', '-w'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from file or return defaults with validation"""
    if config_path is None:
        config_path = os.path.expanduser('~/.grok_terminal_config.json')
    else:
        config_path = os.path.expanduser(config_path)
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                config = DEFAULT_CONFIG.copy()
                
                # Validate and update config
                for key, value in user_config.items():
                    if key not in DEFAULT_CONFIG:
                        continue  # Skip unknown keys
                    
                    # Validate value types and ranges
                    if key == "temperature" and (not isinstance(value, (int, float)) or not 0 <= value <= 2):
                        continue  # Invalid temperature, use default
                    if key == "max_tokens" and (not isinstance(value, int) or value <= 0 or value > 100000):
                        continue  # Invalid max_tokens, use default
                    if key in ["cache_size", "cache_ttl", "max_retries"] and (not isinstance(value, int) or value <= 0):
                        continue  # Invalid numeric values
                    if key == "model" and not isinstance(value, str):
                        continue  # Invalid model name
                    if key == "api_endpoint" and not isinstance(value, str):
                        continue  # Invalid endpoint URL
                    if key == "agent_endpoints" and not isinstance(value, dict):
                        continue  # Invalid agent endpoints mapping
                    if key in ["auto_log", "dangerous_commands_require_flag", "cache_enabled", "health_check_enabled"] and not isinstance(value, bool):
                        continue  # Invalid boolean
                    
                    config[key] = value
                
                return config
        except (json.JSONDecodeError, IOError, OSError):
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

def load_history() -> List[Dict[str, str]]:
    """
    Load conversation history with corruption detection and validation.
    
    Returns:
        List of validated conversation messages. Returns empty list on corruption.
    """
    history_path = Path(os.path.expanduser(DEFAULT_CONFIG['history_file']))
    if history_path.exists():
        try:
            with open(history_path, 'r') as f:
                # Acquire shared lock for reading
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                except (IOError, OSError) as e:
                    logger.debug(f"Could not acquire read lock: {e}")
                    # Continue without lock if not supported
                
                try:
                    data = json.load(f)
                    # Validate structure
                    if not isinstance(data, list):
                        logger.warning("History file contains non-list data, returning empty")
                        return []
                    # Validate each entry
                    validated = []
                    for i, entry in enumerate(data):
                        if isinstance(entry, dict) and 'role' in entry and 'content' in entry:
                            if entry['role'] in ['user', 'assistant', 'system']:
                                validated.append(entry)
                            else:
                                logger.warning(f"Invalid role '{entry['role']}' in history entry {i}")
                        else:
                            logger.warning(f"Invalid history entry {i}: missing role or content")
                    logger.debug(f"Loaded {len(validated)} history messages")
                    return validated
                finally:
                    try:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                    except (IOError, OSError):
                        pass
        except json.JSONDecodeError as e:
            logger.error(f"History file corrupted (invalid JSON): {e}")
            return []
        except (IOError, OSError) as e:
            logger.error(f"Error reading history file: {e}")
            return []
    return []

def save_history(history: List[Dict[str, str]]) -> None:
    """
    Save conversation history with file locking and atomic writes.
    
    Args:
        history: List of conversation messages to save (saves last HISTORY_MESSAGE_LIMIT messages)
        
    Note:
        Failures are logged but don't raise exceptions (non-critical operation)
    """
    history_path = Path(os.path.expanduser(DEFAULT_CONFIG['history_file']))
    try:
        # Atomic write with locking: write to temp file, then rename
        temp_file = history_path.with_suffix('.tmp')
        
        with open(temp_file, 'w') as f:
            # Acquire exclusive lock (non-blocking on macOS/Linux)
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except (IOError, OSError) as e:
                logger.warning(f"Could not acquire file lock: {e}")
                # Continue without lock (better than failing completely)
            
            try:
                json.dump(history[-HISTORY_MESSAGE_LIMIT:], f, indent=2)
            finally:
                # Release lock if acquired
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                except (IOError, OSError):
                    pass
        
        # Set secure permissions before rename
        os.chmod(temp_file, 0o600)
        
        # Atomic rename (atomic on POSIX systems)
        temp_file.replace(history_path)
        
        # Ensure final file has correct permissions
        try:
            os.chmod(history_path, 0o600)
        except OSError as e:
            logger.warning(f"Could not set file permissions: {e}")
        
        logger.debug(f"History saved ({len(history[-HISTORY_MESSAGE_LIMIT:])} messages)")
    except Exception as e:
        logger.error(f"Failed to save history: {e}", exc_info=True)
        # Silent failure is acceptable for history saves (non-critical)

def load_todos() -> Dict[str, Any]:
    """Load todos from persistence"""
    todos_path = os.path.expanduser(DEFAULT_CONFIG['todos_file'])
    if os.path.exists(todos_path):
        try:
            with open(todos_path, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_todos(todos: Dict[str, Any]) -> None:
    """Save todos to persistence with file locking"""
    todos_path = Path(os.path.expanduser(DEFAULT_CONFIG['todos_file']))
    try:
        os.makedirs(os.path.dirname(todos_path), exist_ok=True)
        
        # Atomic write with locking
        temp_file = todos_path.with_suffix('.tmp')
        
        with open(temp_file, 'w') as f:
            # Acquire exclusive lock
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except (IOError, OSError):
                pass
            
            try:
                json.dump(todos, f, indent=2)
            finally:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                except (IOError, OSError):
                    pass
        
        os.chmod(temp_file, 0o600)
        temp_file.replace(todos_path)
        
        try:
            os.chmod(todos_path, 0o600)
        except OSError:
            pass
    except Exception:
        pass

def health_check_api(api_key: str, config: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
    """Health check for API endpoint"""
    if config is None:
        config = DEFAULT_CONFIG
    
    try:
        # Lightweight ping call
        test_response = call_grok_api(
            api_key,
            [{"role": "user", "content": "ping"}],
            config.get("model", "grok-4.1-fast"),
            0.0,
            10,
            stream=False,
            config=config
        )
        return True, "API healthy"
    except Exception as e:
        return False, f"API unhealthy: {str(e)}"


def health_check_keychain() -> Tuple[bool, str]:
    """Health check for Keychain access"""
    try:
        key = get_api_key()
        if key:
            return True, "Keychain accessible"
        return False, "API key not found in Keychain"
    except Exception as e:
        return False, f"Keychain error: {str(e)}"


def health_check_filesystem() -> Tuple[bool, str]:
    """Health check for filesystem operations"""
    try:
        # Test write/read
        test_file = Path.home() / ".grok_terminal" / ".health_check"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("test")
        content = test_file.read_text()
        test_file.unlink()
        if content == "test":
            return True, "Filesystem accessible"
        return False, "Filesystem write/read failed"
    except Exception as e:
        return False, f"Filesystem error: {str(e)}"


def health_check_all(api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> Dict[str, Tuple[bool, str]]:
    """Run all health checks"""
    results = {}
    
    # Keychain check
    keychain_ok, keychain_msg = health_check_keychain()
    results['keychain'] = (keychain_ok, keychain_msg)
    
    # Filesystem check
    fs_ok, fs_msg = health_check_filesystem()
    results['filesystem'] = (fs_ok, fs_msg)
    
    # API check (if key available)
    if api_key:
        api_ok, api_msg = health_check_api(api_key, config)
        results['api'] = (api_ok, api_msg)
    elif keychain_ok:
        api_key = get_api_key()
        if api_key:
            api_ok, api_msg = health_check_api(api_key, config)
            results['api'] = (api_ok, api_msg)
        else:
            results['api'] = (False, "No API key available")
    else:
        results['api'] = (False, "Keychain not accessible")
    
    return results


def get_env_context() -> Tuple[str, str, str]:
    """Get environment context (cwd, git status, dir tree)"""
    cwd = os.getcwd()
    
    # Git status
    try:
        git_result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True, timeout=5)
        git_status = git_result.stdout if git_result.returncode == 0 else "Not a git repository"
    except Exception:
        git_status = "Git status unavailable"
    
    # Dir tree (limit depth 2, fallback to ls if tree not available)
    try:
        tree_result = subprocess.run(['tree', '-L', '2', '-a'], capture_output=True, text=True, timeout=5)
        if tree_result.returncode == 0:
            dir_tree = tree_result.stdout[:500]  # Limit length
        else:
            raise subprocess.CalledProcessError(1, 'tree')
    except Exception:
        # Fallback to ls -la
        try:
            ls_result = subprocess.run(['ls', '-la'], capture_output=True, text=True, timeout=5)
            dir_tree = ls_result.stdout[:500] if ls_result.returncode == 0 else "Directory listing unavailable"
        except Exception:
            dir_tree = "Directory listing unavailable"
    
    return cwd, git_status, dir_tree

def _get_http_client() -> httpx.Client:
    """Get or create HTTP client with connection pooling"""
    global _http_client
    if _http_client is None:
        try:
            # Try to enable HTTP/2 if h2 package is available
            _http_client = httpx.Client(
                timeout=60.0,
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
                http2=True  # HTTP/2 for better performance
            )
        except (ImportError, ValueError):
            # Fall back to HTTP/1.1 if h2 is not installed
            _http_client = httpx.Client(
                timeout=60.0,
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
                http2=False  # HTTP/1.1 fallback
            )
    return _http_client


def _semantic_hash(messages: List[Dict[str, str]], model: str, temperature: float) -> str:
    """Create semantic hash for cache key (normalize query)
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model name
        temperature: Temperature setting (rounded to 2 decimals)
        
    Returns:
        MD5 hash of normalized cache key
    """
    # Normalize messages: lowercase, remove extra spaces, normalize whitespace
    normalized = []
    for msg in messages:
        content = msg.get('content', '').lower().strip()
        # Remove extra whitespace (multiple spaces, tabs, newlines -> single space)
        content = ' '.join(content.split())
        normalized.append({'role': msg.get('role', 'user'), 'content': content})
    
    # Create hash with sorted keys for consistency
    cache_key = json.dumps({
        'messages': normalized,
        'model': model,
        'temperature': round(temperature, 2)  # Round to avoid float precision issues
    }, sort_keys=True)
    
    return hashlib.md5(cache_key.encode()).hexdigest()


def _check_cache(cache_key: str, ttl: float, use_disk: bool = False) -> Optional[Any]:
    """Check if response is in cache and still valid (LRU: move to end on access)
    
    Args:
        cache_key: Cache key (semantic hash)
        ttl: Time-to-live in seconds
        use_disk: Use disk cache if available
        
    Returns:
        Cached response if valid, None otherwise
    """
    # Try disk cache first if enabled
    if use_disk and DISK_CACHE_AVAILABLE:
        global _disk_cache
        if _disk_cache is None:
            _disk_cache = get_disk_cache(max_size=100, ttl=ttl)
        cached = _disk_cache.get(cache_key)
        if cached is not None:
            return cached
    
    # Fallback to in-memory cache
    if cache_key in _response_cache:
        timestamp, response = _response_cache[cache_key]
        if time.time() - timestamp < ttl:
            # Move to end (most recently used) - LRU behavior
            _response_cache.move_to_end(cache_key)
            _cache_stats["hits"] += 1
            return response
        else:
            # Expired, remove from cache
            del _response_cache[cache_key]
    
    _cache_stats["misses"] += 1
    return None


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics
    
    Returns:
        Dict with cache statistics: hits, misses, evictions, size, hit_rate
    """
    total_requests = _cache_stats["hits"] + _cache_stats["misses"]
    hit_rate = _cache_stats["hits"] / total_requests if total_requests > 0 else 0.0
    
    return {
        "hits": _cache_stats["hits"],
        "misses": _cache_stats["misses"],
        "evictions": _cache_stats["evictions"],
        "size": len(_response_cache),
        "hit_rate": hit_rate,
        "total_requests": total_requests
    }


def reset_cache() -> None:
    """Reset cache and statistics (useful for testing)"""
    global _response_cache, _cache_stats
    _response_cache.clear()
    _cache_stats = {"hits": 0, "misses": 0, "evictions": 0}


def _update_cache(cache_key: str, response: Any, max_size: int, use_disk: bool = False) -> None:
    """Update cache with response, evict oldest (LRU) if full
    
    Args:
        cache_key: Cache key (semantic hash)
        response: Response to cache
        max_size: Maximum cache size
        use_disk: Use disk cache if available
    """
    # Use disk cache if enabled
    if use_disk and DISK_CACHE_AVAILABLE:
        global _disk_cache
        if _disk_cache is None:
            _disk_cache = get_disk_cache(max_size=max_size, ttl=300.0)
        _disk_cache.set(cache_key, response)
        return
    
    # Fallback to in-memory cache
    # Remove key if exists (to move to end)
    if cache_key in _response_cache:
        del _response_cache[cache_key]
    
    # Add to end (most recently used)
    _response_cache[cache_key] = (time.time(), response)
    
    # Evict oldest entries (from front) if cache is full - true LRU
    while len(_response_cache) > max_size:
        _response_cache.popitem(last=False)  # Remove oldest (first item)
        _cache_stats["evictions"] += 1


def _retry_with_backoff(func: Any, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0) -> Any:
    """Retry function with exponential backoff and jitter"""
    for attempt in range(max_retries):
        try:
            return func()
        except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as e:
            if attempt == max_retries - 1:
                raise
            
            # Exponential backoff with jitter
            delay = min(base_delay * (2 ** attempt), max_delay)
            jitter = random.uniform(0, RETRY_JITTER_PERCENT * delay)
            total_delay = delay + jitter
            
            time.sleep(total_delay)
        except httpx.HTTPStatusError as e:
            # Don't retry on 4xx errors (client errors)
            if 400 <= e.response.status_code < 500:
                raise
            # Retry on 5xx errors (server errors) and rate limits (429)
            if e.response.status_code == 429 or e.response.status_code >= 500:
                if attempt == max_retries - 1:
                    raise
                delay = min(base_delay * (2 ** attempt), max_delay)
                jitter = random.uniform(0, 0.3 * delay)
                time.sleep(delay + jitter)
            else:
                raise


def call_grok_api(
    api_key: str,
    messages: List[Dict[str, str]],
    model: str,
    temperature: float,
    max_tokens: int,
    stream: bool = False,
    config: Optional[Dict[str, Any]] = None
) -> Any:
    """Call NextEleven API (or custom endpoint) with streaming support, caching, and retry logic"""
    if config is None:
        config = DEFAULT_CONFIG
    
    # Support custom endpoints via config or agent mapping
    url = config.get("api_endpoint", API_ENDPOINT)
    
    # Check if model maps to a specialized agent endpoint
    agent_endpoints = config.get("agent_endpoints", {})
    if model in agent_endpoints:
        url = agent_endpoints[model]
        logger.info(f"Using specialized agent endpoint for {model}: {url}")
    
    # Detect Grok-Code API format (grokcode.vercel.app/api/chat or any custom Grok-Code endpoint)
    # Also detect if using Grok-Code orchestrator by default
    is_grokcode_api = ("grokcode.vercel.app" in url or 
                       url.endswith("/api/chat") or 
                       config.get("use_grokcode_orchestrator", False))
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Convert payload format based on API type
    if is_grokcode_api:
        # Grok-Code API expects: {"message": "string", "model": "...", "mode": "...", "agent": "..."}
        # Extract the last user message or combine all messages
        message_text = ""
        for msg in messages:
            if msg.get("role") == "user":
                message_text = msg.get("content", "")
            elif msg.get("role") == "assistant":
                # Include assistant context if needed
                pass
        
        # If no user message found, combine all messages
        if not message_text:
            message_text = "\n".join([msg.get("content", "") for msg in messages if msg.get("content")])
    
        payload = {
            "message": message_text,
            "model": model,
        }
        
        # Grok-Code workflow: All initial requests go to orchestrator by default
        # Orchestrator analyzes the request and assigns the proper specialized agent automatically
        specialized_agents = config.get("specialized_agents", DEFAULT_CONFIG.get("specialized_agents", {}))
        
        # Check if user explicitly requested a specific agent via --model flag
        # Only if explicitly specified should we bypass orchestrator and go directly to that agent
        explicit_agent_requested = config.get("_explicit_agent_requested", False)
        if explicit_agent_requested and model in specialized_agents and model != "orchestrator":
            # User explicitly requested a specific agent via --model flag - use it directly (bypass orchestrator)
            agent_info = specialized_agents[model]
            payload["mode"] = agent_info.get("mode", "agent")
            payload["agent"] = agent_info.get("agent", model)
            logger.info(f"Using specialized agent (explicit): {agent_info.get('name', model)} ({agent_info.get('emoji', '')})")
        else:

            # Default: Use orchestrator mode (all requests go through orchestrator first)
            # Orchestrator analyzes the message and assigns the appropriate specialized agent
            # This matches Grok-Code behavior where orchestrator handles all routing
            payload["mode"] = "orchestrate"  # Orchestrator decides which agent to use based on message
            # Don't set "agent" parameter - let orchestrator choose based on message content and keywords
            logger.info("Using orchestrator mode (default) - orchestrator will analyze and assign appropriate specialized agent")
        
        # Grok-Code API may not support temperature/max_tokens in the same way
        if temperature != DEFAULT_CONFIG.get("temperature", 0.1):
            payload["temperature"] = temperature
        if max_tokens != DEFAULT_CONFIG.get("max_tokens", 2048):
            payload["max_tokens"] = max_tokens
    else:
        # Standard xAI API format
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
    max_retries = config.get("max_retries", 3)
    base_delay = config.get("retry_base_delay", 1.0)
    max_delay = config.get("retry_max_delay", 60.0)
    
    # Check cache for non-streaming requests
    if not stream and config.get("cache_enabled", True):
        cache_key = _semantic_hash(messages, model, temperature)
        
        # Check for duplicate in-flight requests (request deduplication)
        with _in_flight_lock:
            if cache_key in _in_flight_requests:
                logger.info(f"Deduplicating request: {cache_key[:8]}...")
                # Wait for in-flight request to complete
                import time as time_module
                while cache_key in _in_flight_requests:
                    time_module.sleep(0.1)
                # Try cache again (in-flight request should have cached it)
                cached_response = _check_cache(cache_key, config.get("cache_ttl", 300), config.get("cache_disk", False))
                if cached_response is not None:
                    return cached_response
        
        # Check cache
        cached_response = _check_cache(cache_key, config.get("cache_ttl", 300), config.get("cache_disk", False))
        if cached_response is not None:
            return cached_response
        
        # Mark request as in-flight (for deduplication)
        with _in_flight_lock:
            _in_flight_requests[cache_key] = True
    
    if stream:
        # Streaming response with retry
        def _stream_request() -> Iterator[Dict[str, Any]]:
            client = _get_http_client()
            with client.stream("POST", url, headers=headers, json=payload, timeout=60.0) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line.strip() and line.startswith('data: '):
                        if line.strip() == 'data: [DONE]':
                            break
                        try:
                            data = json.loads(line[6:])  # Remove 'data: ' prefix
                            
                            # Convert Grok-Code format to xAI format for compatibility
                            if is_grokcode_api and "content" in data:
                                # Grok-Code returns: {"content": "text"}
                                # Convert to xAI format: {"choices": [{"delta": {"content": "text"}}]}
                                yield {
                                    "choices": [{
                                        "delta": {
                                            "content": data.get("content", "")
                                        }
                                    }]
                                }
                            else:
                                # Standard xAI format
                                yield data
                        except json.JSONDecodeError:
                            continue
                    
        # Retry wrapper for streaming
        for attempt in range(max_retries):
            try:
                return _stream_request()  # Return generator
            except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError, httpx.HTTPStatusError) as e:
                if isinstance(e, httpx.HTTPStatusError):
                    if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                        raise ValueError(f"API request failed: {e.response.status_code}")
                    if e.response.status_code != 429 and e.response.status_code < 500:
                        raise
                
                if attempt == max_retries - 1:
                    if isinstance(e, httpx.HTTPStatusError):
                        if e.response.status_code == 401:
                            raise ValueError("Invalid API key. Please check your NextEleven API key.")
                        elif e.response.status_code == 429:
                            raise ValueError("Rate limit exceeded. Please wait before trying again.")
                    raise ValueError(f"API request failed after {max_retries} retries: {str(e)}")
                
                delay = min(base_delay * (2 ** attempt), max_delay)
                jitter = random.uniform(0, 0.3 * delay)
                time.sleep(delay + jitter)
    else:
        # Non-streaming with retry and caching
        try:
            response = _retry_with_backoff(
                lambda: _get_http_client().post(url, headers=headers, json=payload, timeout=60.0),
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay
            )
            response.raise_for_status()
            result = response.json()
            
            # Convert Grok-Code format to xAI format for compatibility
            if is_grokcode_api:
                # Grok-Code may return different format, convert to xAI format
                if "content" in result:
                    # Convert: {"content": "text"} -> {"choices": [{"message": {"content": "text"}}]}
                    result = {
                        "choices": [{
                            "message": {
                                "content": result.get("content", "")
                            }
                        }]
                    }
                elif "message" in result:
                    # Alternative format
                    result = {
                        "choices": [{
                            "message": {
                                "content": result.get("message", "")
                            }
                        }]
                    }
            
            # Cache response
            if config.get("cache_enabled", True):
                cache_key = _semantic_hash(messages, model, temperature)
                _update_cache(cache_key, result, config.get("cache_size", 100), config.get("cache_disk", False))
                
                # Remove from in-flight requests (deduplication)
                with _in_flight_lock:
                    _in_flight_requests.pop(cache_key, None)
            
            return result
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ValueError("Invalid API key. Please check your NextEleven API key.")
            elif e.response.status_code == 429:
                raise ValueError("Rate limit exceeded. Please wait before trying again.")
            else:
                raise ValueError(f"API request failed: {e.response.status_code} {e.response.text}")

def extract_tools(response: str) -> List[Tuple[str, List[Tuple[str, str]]]]:
    """Parse <tool name="..."><param>...</tool> from response"""
    tools = []
    pattern = r'<tool name="(\w+)">(.*?)</tool>'
    matches = re.findall(pattern, response, re.DOTALL)
    
    for name, params_str in matches:
        param_pattern = r'<param name="(\w+)">(.*?)</param>'
        params = re.findall(param_pattern, params_str, re.DOTALL)
        tools.append((name, params))
    
    return tools

def classify_command_risk(cmd: str) -> str:
    """Classify command risk level"""
    cmd_lower = cmd.lower()
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd_lower):
            return "DANGEROUS"
    if "ls" in cmd_lower or "cat" in cmd_lower or "echo" in cmd_lower:
        return "SAFE"
    return "CAUTION"

def run_hook(hook_type: str, data: Dict[str, Any]) -> Tuple[bool, str]:
    """Run pre/post tool hooks from ~/.grok_terminal/hooks/"""
    hook_dir = os.path.expanduser(DEFAULT_CONFIG['hooks_dir'])
    hook_file = os.path.join(hook_dir, f"{hook_type}.sh")
    
    if os.path.exists(hook_file):
        try:
            proc = subprocess.Popen(
                ['/bin/bash', hook_file],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            output, error = proc.communicate(json.dumps(data), timeout=30)
            return proc.returncode == 0, output or error
        except subprocess.TimeoutExpired:
            return False, "Hook timeout"
        except Exception as e:
            return False, str(e)
    return True, ""


def export_user_data() -> None:
    """Export all user data for GDPR/CCPA compliance
    
    Exports:
    - Conversation history
    - Configuration
    - Todos
    - Logs (if available)
    """
    export_data = {
        "export_date": datetime.now().isoformat(),
        "version": "1.0",
        "data": {}
    }
    
    # Export history
    history_path = os.path.expanduser(DEFAULT_CONFIG['history_file'])
    if os.path.exists(history_path):
        try:
            with open(history_path, 'r') as f:
                export_data["data"]["history"] = json.load(f)
        except Exception as e:
            logger.error(f"Error exporting history: {e}")
            export_data["data"]["history"] = None
    
    # Export config
    config_path = os.path.expanduser('~/.grok_terminal_config.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                export_data["data"]["config"] = json.load(f)
        except Exception as e:
            logger.error(f"Error exporting config: {e}")
            export_data["data"]["config"] = None
    
    # Export todos
    todos_path = os.path.expanduser(DEFAULT_CONFIG['todos_file'])
    if os.path.exists(todos_path):
        try:
            with open(todos_path, 'r') as f:
                export_data["data"]["todos"] = json.load(f)
        except Exception as e:
            logger.error(f"Error exporting todos: {e}")
            export_data["data"]["todos"] = None
    
    # Export logs (last 100 lines)
    log_path = os.path.expanduser('~/.grok_terminal/grok.log')
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r') as f:
                lines = f.readlines()
                export_data["data"]["logs"] = lines[-100:] if len(lines) > 100 else lines
        except Exception as e:
            logger.error(f"Error exporting logs: {e}")
            export_data["data"]["logs"] = None
    
    # Write export file
    export_file = os.path.expanduser('~/.grok_terminal_data_export.json')
    try:
        with open(export_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        print(colored(f"✓ Data exported to: {export_file}", 'green'))
        print(colored(f"  Export includes: history, config, todos, logs", 'cyan'))
    except Exception as e:
        print(colored(f"✗ Error exporting data: {e}", 'red'))
        sys.exit(1)


def delete_user_data() -> None:
    """Delete all user data for GDPR/CCPA compliance
    
    Deletes:
    - Conversation history
    - Configuration
    - Todos
    - Logs (if requested)
    
    Note: API key is NOT deleted (user must delete manually from Keychain)
    """
    print(colored("⚠️  WARNING: This will delete all user data!", 'yellow'))
    print(colored("  - Conversation history", 'yellow'))
    print(colored("  - Configuration", 'yellow'))
    print(colored("  - Todos", 'yellow'))
    print(colored("  - Logs", 'yellow'))
    print(colored("  Note: API key will NOT be deleted (delete manually from Keychain)", 'yellow'))
    print()
    
    confirmation = input(colored("Type 'DELETE' to confirm: ", 'red'))
    
    if confirmation != 'DELETE':
        print(colored("Cancelled. No data deleted.", 'green'))
        return
    
    deleted_files = []
    
    # Delete history
    history_path = os.path.expanduser(DEFAULT_CONFIG['history_file'])
    if os.path.exists(history_path):
        try:
            os.remove(history_path)
            deleted_files.append("history")
        except Exception as e:
            logger.error(f"Error deleting history: {e}")
    
    # Delete config
    config_path = os.path.expanduser('~/.grok_terminal_config.json')
    if os.path.exists(config_path):
        try:
            os.remove(config_path)
            deleted_files.append("config")
        except Exception as e:
            logger.error(f"Error deleting config: {e}")
    
    # Delete todos
    todos_path = os.path.expanduser(DEFAULT_CONFIG['todos_file'])
    if os.path.exists(todos_path):
        try:
            os.remove(todos_path)
            deleted_files.append("todos")
        except Exception as e:
            logger.error(f"Error deleting todos: {e}")
    
    # Delete logs
    log_path = os.path.expanduser('~/.grok_terminal/grok.log')
    if os.path.exists(log_path):
        try:
            os.remove(log_path)
            deleted_files.append("logs")
        except Exception as e:
            logger.error(f"Error deleting logs: {e}")
    
    # Reset cache
    reset_cache()
    
    if deleted_files:
        print(colored(f"✓ Deleted: {', '.join(deleted_files)}", 'green'))
        print(colored("  Note: API key is still in Keychain (delete manually if needed)", 'cyan'))
    else:
        print(colored("  No data files found to delete.", 'cyan'))

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='NextEleven Terminal Agent (eleven-powered)')
    parser.add_argument('--interactive', action='store_true', help='Start interactive mode')
    parser.add_argument('--dangerously-skip-permissions', action='store_true', help='Skip permission prompts')
    parser.add_argument('--no-log', action='store_true', help='Disable logging')
    parser.add_argument('--force', action='store_true', help='Allow dangerous commands')
    parser.add_argument('--verify-creator', action='store_true', help='Verify creator identity')
    parser.add_argument('--model', type=str, help='Override model name (e.g., grok-4.1-fast, or specialized agent: security, performance, testing, etc.)')
    parser.add_argument('--config', type=str, help='Use specific config file path')
    parser.add_argument('--endpoint', type=str, help='Override API endpoint (e.g., https://grokcode.vercel.app/api/chat)')
    parser.add_argument('--list-agents', action='store_true', help='List all available specialized agents')
    parser.add_argument('--export-data', action='store_true', help='Export all user data (GDPR/CCPA compliance)')
    parser.add_argument('--delete-data', action='store_true', help='Delete all user data (GDPR/CCPA compliance)')
    parser.add_argument('--chain', nargs='+', help='Chain multiple agents (e.g., --chain security performance testing)')
    parser.add_argument('--local-llm', action='store_true', help='Enable local LLM (Ollama)')
    parser.add_argument('--local-llm-model', type=str, default='llama3.2', help='Local LLM model name')
    parser.add_argument('--image', action='append', help='Add image file to message (can be used multiple times)')
    parser.add_argument('--file', action='append', help='Add file to message (can be used multiple times)')
    parser.add_argument('query', nargs='*', help='Query for non-interactive mode')
    args = parser.parse_args()

    # Handle creator verification
    if args.verify_creator:
        try:
            from identity_verify import verify_creator
            is_verified, message = verify_creator()
            print(message)
            if is_verified:
                print(f"\n✓ Creator identity verified. All restrictions bypassed.")
                print(f"You now have full override access to the system.")
            sys.exit(0 if is_verified else 1)
        except ImportError:
            print("Error: identity_verify module not found", file=sys.stderr)
            sys.exit(1)

    # Load config (use custom path if provided)
    config = load_config(args.config)
    
    # List specialized agents if requested (before API key check)
    if args.list_agents:
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
    
    # GDPR/CCPA Compliance: Export data
    if args.export_data:
        export_user_data()
        sys.exit(0)
    
    # GDPR/CCPA Compliance: Delete data
    if args.delete_data:
        delete_user_data()
        sys.exit(0)

    api_key = get_api_key()
    if not api_key:
        error_msg = "NextEleven API key not found in Keychain. Run install.sh to set up your API key."
        logger.error(error_msg)
        print(colored(f"Error: {error_msg}", 'red'))
        sys.exit(1)
    
    # Override endpoint if specified via --endpoint flag
    if args.endpoint:
        config['api_endpoint'] = args.endpoint
        logger.info(f"Using endpoint override: {args.endpoint}")
    
    # Detect project types for orchestrator context (informational only - orchestrator will assign agents)
    # The orchestrator will use project detection info in system prompt to auto-assign appropriate agents
    detected_project_type = None
    if not args.model:
        try:
            from xcode_utils import find_xcode_project
            xcode_project = find_xcode_project(os.getcwd())
            if xcode_project:
                detected_project_type = 'xcode'
                logger.info(f"Xcode project detected: {xcode_project} (orchestrator will assign xcode agent if needed)")
                print(colored(f"📱 Xcode project detected - orchestrator will assign Xcode Expert Agent if needed", 'cyan'))
        except ImportError:
            pass  # xcode_utils not available
        
        if not detected_project_type:
            try:
                from android_utils import find_android_project
                android_project = find_android_project(os.getcwd())
                if android_project:
                    detected_project_type = 'android'
                    logger.info(f"Android project detected: {android_project} (orchestrator will assign android agent if needed)")
                    print(colored(f"🤖 Android project detected - orchestrator will assign Android Expert Agent if needed", 'cyan'))
            except ImportError:
                pass  # android_utils not available
    
    # Grok-Code workflow: All initial requests go to orchestrator by default
    # Orchestrator will auto-assign agents (including xcode/android) based on context in system prompt
    # Only if user explicitly requests a specific agent via --model should we bypass orchestrator
    explicit_agent_requested = False
    if args.model:
        config['model'] = args.model
        specialized_agents = config.get("specialized_agents", DEFAULT_CONFIG.get("specialized_agents", {}))
        if args.model in specialized_agents:
            # User explicitly requested a specific specialized agent - use it directly
            explicit_agent_requested = True
            config['_explicit_agent_requested'] = True
            logger.info(f"Explicit agent requested: {specialized_agents[args.model].get('name', args.model)}")
        else:
            # Model is not a specialized agent (e.g., "grok-4.1-fast") - use orchestrator (default)
            config['_explicit_agent_requested'] = False
            logger.info(f"Using model: {args.model} (default: orchestrator will assign agent)")
    else:
        # No --model flag: use orchestrator by default (Grok-Code behavior)
        # Orchestrator will analyze context (including project detection in system prompt) and assign appropriate agent
        config['_explicit_agent_requested'] = False
        if detected_project_type:
            logger.info(f"Using orchestrator by default - orchestrator will auto-assign {detected_project_type} agent based on detected project")
        else:
            logger.info("Using orchestrator by default (Grok-Code behavior - orchestrator assigns agents based on context)")
    
    # Enable local LLM if requested
    if args.local_llm:
        config['local_llm_enabled'] = True
        config['local_llm_model'] = args.local_llm_model
        logger.info(f"Local LLM enabled with model: {args.local_llm_model}")
    
    history = load_history()
    todos = load_todos()

    # Handle agent chaining (Phase 4.2)
    if args.chain and AGENT_CHAINING_AVAILABLE:
        query = ' '.join(args.query) if args.query else input("Enter query: ").strip()
        if not query:
            print(colored("Error: Query required for agent chaining", 'red'))
            sys.exit(1)
        
        try:
            result = chain_agents(args.chain, query, config)
            print(colored(f"\nFinal Result:\n{result['final_result']}", 'green'))
            if result.get('intermediate_results'):
                print(colored("\nIntermediate Results:", 'cyan'))
                for i, res in enumerate(result['intermediate_results'], 1):
                    agent = res.get('agent', 'unknown')
                    if 'error' in res:
                        print(colored(f"  {i}. {agent}: ERROR - {res['error']}", 'red'))
                    else:
                        print(colored(f"  {i}. {agent}: {res.get('result', '')[:100]}...", 'yellow'))
            sys.exit(0 if result.get('success') else 1)
        except Exception as e:
            print(colored(f"Agent chaining error: {e}", 'red'))
            sys.exit(1)

    if args.interactive:
        # Start/decline prompt (exact Claude match)
        print(colored("Start eleven Terminal Agent session?", 'yellow'))
        print("This allows API calls, file operations, and commands.")
        print("1. Yes")
        print("2. Decline")
        choice = input("> ").strip().lower()
        # Accept "1", "yes", "y" as affirmative
        if choice not in ['1', 'yes', 'y']:
            print("Declined.")
            sys.exit(0)
    
        # Quota check (emulate Claude's lightweight call)
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

        # Summarize previous if history exists (emulate Claude's compact)
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

        print(colored("eleven session started. Type queries; /help for commands; 'exit' to quit.", 'green'))

        while True:
            try:
                user_input = input(colored("You: ", 'blue')).strip()
                
                if user_input.lower() == 'exit':
                    save_history(history)
                    save_todos(todos)
                    print(colored("Session ended.", 'green'))
                    break

                # Slash commands (Claude-like) - use helper if available
                if user_input.startswith('/'):
                    if MAIN_HELPERS_AVAILABLE and handle_slash_commands(user_input, api_key, config, history, args):
                        continue
                    # Fallback to inline implementation
                    if user_input == '/help':
                        print(colored("Commands:", 'cyan'))
                        print("  /init  - Generate ELEVEN.md with project instructions/tools")
                        print("  /clear - Reset conversation history")
                        print("  /hooks - Configure hooks (see ~/.grok_terminal/hooks/ for details)")
                    elif user_input == '/init':
                        # Generate ELEVEN.md (emulate /init)
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
                    elif user_input == '/clear':
                        history = [history[0]] if history and history[0].get('role') == 'system' else []
                        print(colored("History cleared.", 'green'))
                    elif user_input == '/hooks':
                        hook_dir = os.path.expanduser(DEFAULT_CONFIG['hooks_dir'])
                        print(colored(f"Hooks directory: {hook_dir}", 'cyan'))
                        print("Create PreToolUse.sh and PostToolUse.sh in this directory")
                    continue

                # Topic detection (lightweight call)
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
                    # Build params dict
                    params = {p[0]: p[1] for p in params_list}
                    
                    # Validate tool parameters (Phase 3.3)
                    if VALIDATION_AVAILABLE and validate_tool_params:
                        # Basic validation
                        if tool_name == "Bash" and validate_command:
                            valid, error = validate_command(params.get("command", ""))
                            if not valid:
                                print(colored(f"Invalid command: {error}", 'red'))
                                continue
                        elif tool_name in ["View", "Edit", "Write", "LS", "Glob", "Grep"] and validate_file_path:
                            path = params.get("path", params.get("file", params.get("dir", ".")))
                            valid, error = validate_file_path(path, must_exist=(tool_name in ["View", "Edit"]))
                            if not valid:
                                print(colored(f"Invalid path: {error}", 'red'))
                                continue
                    
                    # Use helper function if available, otherwise inline execution
                    if MAIN_HELPERS_AVAILABLE:
                        exit_code, stdout, stderr = execute_tool_safely(tool_name, params, args, history)
                        if exit_code is None:
                            continue  # Tool execution was cancelled or failed validation
                    else:
                        # Check if tool exists in TOOLS or plugin system (Phase 3.2)
                        if tool_name not in TOOLS:
                            # Try plugin system
                            if PLUGIN_SYSTEM_AVAILABLE and plugin_get_tool:
                                plugin_tool = plugin_get_tool(tool_name)
                                if plugin_tool:
                                    try:
                                        exit_code, stdout, stderr = plugin_execute_tool(tool_name, params)
                                        result_text = stdout if stdout else stderr
                                        if exit_code == 0:
                                            print(colored(f"Plugin tool {tool_name} result: {result_text}", 'magenta'))
                                        else:
                                            print(colored(f"Plugin tool {tool_name} error: {result_text}", 'red'))
                                    except Exception as e:
                                        print(colored(f"Plugin tool {tool_name} exception: {e}", 'red'))
                                    continue
                            else:
                                print(colored(f"Unknown tool: {tool_name}", 'red'))
                                continue
                        
                        # Classify risk for Bash commands
                        risk = classify_command_risk(params.get('command', '')) if tool_name == 'Bash' else "SAFE"

                        # Pre-hook
                        pre_ok, pre_out = run_hook("PreToolUse", {"tool": tool_name, "params": params})
                        if not pre_ok:
                            print(colored(f"Pre-hook failed: {pre_out}", 'red'))
                            continue

                        # Permission prompt (unless skipped)
                        if not args.dangerously_skip_permissions and risk != "SAFE" and not args.force:
                            print(colored(f"Allow {tool_name} with params {params}? [y/n]", 'yellow'))
                            if input().lower() != 'y':
                                continue

                        # Execute tool
                        exit_code = 1
                        stdout = ""
                        stderr = ""
                        result_text = ""
                        
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
                        except Exception as e:
                            print(colored(f"Tool {tool_name} exception: {e}", 'red'))
                            result_text = str(e)
                            stderr = str(e)
                            continue

                        # Post-hook (only if tool executed successfully)
                        if exit_code is not None:
                            run_hook("PostToolUse", {"tool": tool_name, "result": result_text if exit_code == 0 else stderr})

                # Compact history if too long (use helper if available)
                if MAIN_HELPERS_AVAILABLE:
                    history = compact_history_if_needed(history, api_key, config)
                else:
                    if len(history) > HISTORY_COMPACT_THRESHOLD:
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
                            history = [history[0]] + [{"role": "assistant", "content": compacted_content}]
                        except Exception:
                            # If compaction fails, just keep recent history
                            history = history[:1] + history[-19:]

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

    else:
        # Non-interactive mode (prefix mode) - single-shot query
        query = ' '.join(args.query) if args.query else ""
        
        if not query:
            parser.print_help()
            sys.exit(1)

        # Similar logic but single-shot
        cwd, git_status, dir_tree = get_env_context()
        system_prompt = get_system_prompt(cwd, git_status, dir_tree)
        
        # Support multi-modal input (Phase 4.3)
        if MULTIMODAL_AVAILABLE and (args.image or args.file):
            messages = create_multimodal_messages(
                query,
                image_paths=args.image or [],
                file_paths=args.file or [],
                system_prompt=system_prompt
            )
        else:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
        
        # Add recent history if available
        if history:
            messages = messages + history[-10:]
        
        try:
            # Stream response
            full_response = ""
            print(colored("eleven: ", 'green'), end='', flush=True)
            for chunk in call_grok_api(api_key, messages, config['model'], config['temperature'], config['max_tokens'], stream=True, config=config):
                content = chunk.get('choices', [{}])[0].get('delta', {}).get('content', '')
                if content:
                    print(content, end='', flush=True)
                    full_response += content
            print()
            
            # Extract commands if any
            tool_calls = extract_tools(full_response)
            if tool_calls:
                print(colored("\nTools detected:", 'cyan'))
                for tool_name, params_list in tool_calls:
                    print(f"  {tool_name}: {dict(params_list)}")
            
            # Update history
            history.append({"role": "user", "content": query})
            history.append({"role": "assistant", "content": full_response})
            save_history(history)
            
        except Exception as e:
            print(colored(f"Error: {e}", 'red'))
            sys.exit(1)

if __name__ == "__main__":
    main()
