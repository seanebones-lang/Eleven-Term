"""Tests for plugin system"""
import pytest
from plugin_system import (
    register_tool, unregister_tool, get_tool, list_tools,
    execute_tool, load_plugin_from_file
)

def test_register_tool():
    """Test tool registration"""
    def test_tool(params):
        return 0, "Success", ""
    
    register_tool("test_tool", test_tool, "Test tool", {"param1": "Test param"})
    
    tool = get_tool("test_tool")
    assert tool is not None
    assert tool["description"] == "Test tool"
    assert "test_tool" in list_tools()
    
    unregister_tool("test_tool")
    assert "test_tool" not in list_tools()

def test_execute_tool():
    """Test tool execution"""
    def test_tool(params):
        return 0, f"Result: {params.get('input', '')}", ""
    
    register_tool("test_tool", test_tool)
    
    exit_code, stdout, stderr = execute_tool("test_tool", {"input": "test"})
    assert exit_code == 0
    assert "test" in stdout
    
    unregister_tool("test_tool")

def test_execute_nonexistent_tool():
    """Test executing non-existent tool"""
    exit_code, stdout, stderr = execute_tool("nonexistent", {})
    assert exit_code == 1
    assert "not found" in stderr

def test_register_invalid_tool():
    """Test registering invalid tool"""
    with pytest.raises(ValueError):
        register_tool("invalid", "not a function")
    
    def wrong_signature(a, b):
        return 0, "", ""
    
    with pytest.raises(ValueError):
        register_tool("wrong", wrong_signature)