"""
Plugin system for grok_agent
Allows users to register custom tools and extend functionality
"""
import inspect
import logging
from typing import Dict, Any, Callable, List, Tuple, Optional
from pathlib import Path
import importlib.util

logger = logging.getLogger(__name__)

# Registry for plugins
_plugin_registry: Dict[str, Dict[str, Any]] = {}

def register_tool(name: str, func: Callable, description: str = "", params: Optional[Dict[str, str]] = None):
    """Register a custom tool
    
    Args:
        name: Tool name (e.g., "custom_tool")
        func: Tool function (must return Tuple[int, str, str] = (exit_code, stdout, stderr))
        description: Tool description
        params: Parameter schema (dict of param_name -> param_description)
    """
    if not callable(func):
        raise ValueError(f"Tool {name} must be a callable function")
    
    # Validate function signature
    sig = inspect.signature(func)
    if len(sig.parameters) != 1:
        raise ValueError(f"Tool {name} must accept exactly one parameter (params: Dict[str, Any])")
    
    _plugin_registry[name] = {
        "func": func,
        "description": description or f"Custom tool: {name}",
        "params": params or {},
        "type": "custom"
    }
    
    logger.info(f"Registered custom tool: {name}")

def unregister_tool(name: str) -> bool:
    """Unregister a custom tool
    
    Args:
        name: Tool name to unregister
        
    Returns:
        True if tool was removed, False if not found
    """
    if name in _plugin_registry:
        del _plugin_registry[name]
        logger.info(f"Unregistered tool: {name}")
        return True
    return False

def get_tool(name: str) -> Optional[Dict[str, Any]]:
    """Get tool by name
    
    Args:
        name: Tool name
        
    Returns:
        Tool dict with func, description, params, or None if not found
    """
    return _plugin_registry.get(name)

def list_tools() -> List[str]:
    """List all registered tools
    
    Returns:
        List of tool names
    """
    return list(_plugin_registry.keys())

def load_plugin_from_file(file_path: str) -> bool:
    """Load plugin from Python file
    
    Args:
        file_path: Path to plugin Python file
        
    Returns:
        True if loaded successfully, False otherwise
    """
    try:
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            logger.error(f"Plugin file not found: {file_path}")
            return False
        
        spec = importlib.util.spec_from_file_location("plugin_module", file_path)
        if spec is None or spec.loader is None:
            logger.error(f"Could not load plugin spec from: {file_path}")
            return False
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Look for register_plugin function
        if hasattr(module, 'register_plugin'):
            module.register_plugin()
            logger.info(f"Loaded plugin from: {file_path}")
            return True
        else:
            logger.warning(f"Plugin file {file_path} has no register_plugin() function")
            return False
    except Exception as e:
        logger.error(f"Error loading plugin from {file_path}: {e}")
        return False

def load_plugins_from_directory(directory: str) -> int:
    """Load all plugins from directory
    
    Args:
        directory: Directory containing plugin files
        
    Returns:
        Number of plugins loaded
    """
    plugin_dir = Path(directory)
    if not plugin_dir.exists():
        logger.warning(f"Plugin directory not found: {directory}")
        return 0
    
    loaded = 0
    for plugin_file in plugin_dir.glob("*.py"):
        if plugin_file.name == "__init__.py":
            continue
        
        if load_plugin_from_file(str(plugin_file)):
            loaded += 1
    
    return loaded

def execute_tool(name: str, params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Execute a registered tool
    
    Args:
        name: Tool name
        params: Tool parameters
        
    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    tool = get_tool(name)
    if tool is None:
        return 1, "", f"Tool '{name}' not found"
    
    try:
        func = tool["func"]
        return func(params)
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        return 1, "", str(e)

# Example plugin format:
"""
# my_plugin.py
from plugin_system import register_tool

def my_custom_tool(params: dict):
    # params is a dict with tool parameters
    # Return (exit_code, stdout, stderr)
    return 0, "Success", ""

def register_plugin():
    register_tool(
        name="my_custom_tool",
        func=my_custom_tool,
        description="My custom tool description",
        params={"param1": "Description of param1"}
    )
"""