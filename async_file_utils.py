"""
Async file I/O utilities for grok_agent
Provides non-blocking file operations for better performance
"""
import aiofiles
import json
import fcntl
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import asyncio

async def async_load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Async load configuration from file
    
    Args:
        config_path: Optional path to config file
        
    Returns:
        Configuration dictionary
    """
    if config_path is None:
        config_path = os.path.expanduser('~/.grok_terminal_config.json')
    else:
        config_path = os.path.expanduser(config_path)
    
    config_path_obj = Path(config_path)
    
    if not config_path_obj.exists():
        return {}
    
    try:
        async with aiofiles.open(config_path, 'r') as f:
            content = await f.read()
            return json.loads(content)
    except (json.JSONDecodeError, IOError, OSError):
        return {}

async def async_load_history(history_file: str) -> List[Dict[str, str]]:
    """Async load conversation history
    
    Args:
        history_file: Path to history file
        
    Returns:
        List of conversation messages
    """
    history_path = Path(os.path.expanduser(history_file))
    
    if not history_path.exists():
        return []
    
    try:
        async with aiofiles.open(history_path, 'r') as f:
            content = await f.read()
            data = json.loads(content)
            
            if not isinstance(data, list):
                return []
            
            # Validate entries
            validated = []
            for entry in data:
                if isinstance(entry, dict) and 'role' in entry and 'content' in entry:
                    if entry['role'] in ['user', 'assistant', 'system']:
                        validated.append(entry)
            
            return validated
    except (json.JSONDecodeError, IOError, OSError):
        return []

async def async_save_history(history: List[Dict[str, str]], history_file: str, max_messages: int = 40) -> None:
    """Async save conversation history with atomic write
    
    Args:
        history: List of conversation messages
        history_file: Path to history file
        max_messages: Maximum messages to save
    """
    history_path = Path(os.path.expanduser(history_file))
    temp_file = history_path.with_suffix('.tmp')
    
    try:
        # Write to temp file
        async with aiofiles.open(temp_file, 'w') as f:
            await f.write(json.dumps(history[-max_messages:], indent=2))
        
        # Set permissions
        os.chmod(temp_file, 0o600)
        
        # Atomic rename
        temp_file.replace(history_path)
        
        # Ensure final permissions
        try:
            os.chmod(history_path, 0o600)
        except OSError:
            pass
    except Exception:
        # Clean up temp file on error
        if temp_file.exists():
            try:
                temp_file.unlink()
            except OSError:
                pass

async def async_load_todos(todos_file: str) -> Dict[str, Any]:
    """Async load todos
    
    Args:
        todos_file: Path to todos file
        
    Returns:
        Todos dictionary
    """
    todos_path = Path(os.path.expanduser(todos_file))
    
    if not todos_path.exists():
        return {}
    
    try:
        async with aiofiles.open(todos_path, 'r') as f:
            content = await f.read()
            return json.loads(content)
    except (json.JSONDecodeError, IOError, OSError):
        return {}

async def async_save_todos(todos: Dict[str, Any], todos_file: str) -> None:
    """Async save todos with atomic write
    
    Args:
        todos: Todos dictionary
        todos_file: Path to todos file
    """
    todos_path = Path(os.path.expanduser(todos_file))
    todos_path.parent.mkdir(parents=True, exist_ok=True)
    
    temp_file = todos_path.with_suffix('.tmp')
    
    try:
        async with aiofiles.open(temp_file, 'w') as f:
            await f.write(json.dumps(todos, indent=2))
        
        os.chmod(temp_file, 0o600)
        temp_file.replace(todos_path)
        
        try:
            os.chmod(todos_path, 0o600)
        except OSError:
            pass
    except Exception:
        if temp_file.exists():
            try:
                temp_file.unlink()
            except OSError:
                pass

async def async_read_file(file_path: str) -> str:
    """Async read file content
    
    Args:
        file_path: Path to file
        
    Returns:
        File content as string
    """
    try:
        async with aiofiles.open(file_path, 'r') as f:
            return await f.read()
    except (IOError, OSError):
        return ""

async def async_write_file(file_path: str, content: str) -> bool:
    """Async write file content
    
    Args:
        file_path: Path to file
        content: Content to write
        
    Returns:
        True if successful, False otherwise
    """
    try:
        file_path_obj = Path(file_path)
        file_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(file_path, 'w') as f:
            await f.write(content)
        
        return True
    except (IOError, OSError):
        return False