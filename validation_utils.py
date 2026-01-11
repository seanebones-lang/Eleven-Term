"""
Enhanced input validation utilities
Comprehensive validation for tool parameters, file paths, commands, etc.
"""
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from urllib.parse import urlparse

def validate_file_path(path: str, must_exist: bool = False, must_be_file: bool = False, must_be_dir: bool = False) -> Tuple[bool, Optional[str]]:
    """Validate file path
    
    Args:
        path: Path to validate
        must_exist: Path must exist
        must_be_file: Path must be a file
        must_be_dir: Path must be a directory
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path or not isinstance(path, str):
        return False, "Path must be a non-empty string"
    
    # Check for path traversal attempts
    if '..' in path or path.startswith('/'):
        # Allow absolute paths but warn about traversal
        if '..' in path:
            return False, "Path traversal ('..') not allowed"
    
    path_obj = Path(path)
    
    if must_exist and not path_obj.exists():
        return False, f"Path does not exist: {path}"
    
    if must_be_file and not path_obj.is_file():
        return False, f"Path is not a file: {path}"
    
    if must_be_dir and not path_obj.is_dir():
        return False, f"Path is not a directory: {path}"
    
    return True, None

def validate_command(cmd: str, max_length: int = 10000) -> Tuple[bool, Optional[str]]:
    """Validate shell command
    
    Args:
        cmd: Command string
        max_length: Maximum command length
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not cmd or not isinstance(cmd, str):
        return False, "Command must be a non-empty string"
    
    if len(cmd) > max_length:
        return False, f"Command too long (max {max_length} characters)"
    
    # Check for dangerous patterns
    dangerous_patterns = [
        r'rm\s+-rf',
        r'sudo\s+',
        r'kill\s+-9',
        r'mkfs\b',
        r'dd\s+if=',
        r'chmod\s+777',
        r'>\s*/dev/',
        r'\bformat\b',
        r'\bfdisk\b',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, cmd, re.IGNORECASE):
            return False, f"Dangerous command pattern detected: {pattern}"
    
    return True, None

def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """Validate URL
    
    Args:
        url: URL string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url or not isinstance(url, str):
        return False, "URL must be a non-empty string"
    
    try:
        result = urlparse(url)
        if not result.scheme or not result.netloc:
            return False, "Invalid URL format (missing scheme or netloc)"
        
        if result.scheme not in ['http', 'https']:
            return False, f"Unsupported URL scheme: {result.scheme}"
        
        return True, None
    except Exception as e:
        return False, f"Invalid URL: {str(e)}"

def validate_tool_params(tool_name: str, params: Dict[str, Any], required_params: List[str], param_types: Dict[str, type]) -> Tuple[bool, Optional[str]]:
    """Validate tool parameters
    
    Args:
        tool_name: Name of tool
        params: Parameters dict
        required_params: List of required parameter names
        param_types: Dict mapping param names to expected types
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(params, dict):
        return False, f"Parameters must be a dictionary for tool {tool_name}"
    
    # Check required parameters
    for param in required_params:
        if param not in params:
            return False, f"Missing required parameter '{param}' for tool {tool_name}"
    
    # Check parameter types
    for param_name, expected_type in param_types.items():
        if param_name in params:
            value = params[param_name]
            if not isinstance(value, expected_type):
                return False, f"Parameter '{param_name}' must be of type {expected_type.__name__} for tool {tool_name}, got {type(value).__name__}"
    
    return True, None

def validate_config_value(key: str, value: Any) -> Tuple[bool, Optional[str]]:
    """Validate configuration value
    
    Args:
        key: Configuration key
        value: Configuration value
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    validators = {
        "temperature": lambda v: isinstance(v, (int, float)) and 0.0 <= v <= 2.0,
        "max_tokens": lambda v: isinstance(v, int) and v > 0,
        "cache_size": lambda v: isinstance(v, int) and v > 0,
        "cache_ttl": lambda v: isinstance(v, (int, float)) and v > 0,
        "max_retries": lambda v: isinstance(v, int) and v >= 0,
        "retry_base_delay": lambda v: isinstance(v, (int, float)) and v > 0,
        "retry_max_delay": lambda v: isinstance(v, (int, float)) and v > 0,
    }
    
    if key in validators:
        if not validators[key](value):
            return False, f"Invalid value for {key}: {value}"
    
    return True, None

def sanitize_path(path: str) -> str:
    """Sanitize file path
    
    Args:
        path: Path to sanitize
        
    Returns:
        Sanitized path
    """
    # Remove null bytes
    path = path.replace('\x00', '')
    
    # Normalize path separators
    path = os.path.normpath(path)
    
    return path.strip()

def validate_json_structure(data: Any, expected_type: type, required_keys: Optional[List[str]] = None) -> Tuple[bool, Optional[str]]:
    """Validate JSON structure
    
    Args:
        data: Data to validate
        expected_type: Expected type (dict, list, etc.)
        required_keys: Required keys if dict
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(data, expected_type):
        return False, f"Expected {expected_type.__name__}, got {type(data).__name__}"
    
    if expected_type == dict and required_keys:
        for key in required_keys:
            if key not in data:
                return False, f"Missing required key: {key}"
    
    return True, None