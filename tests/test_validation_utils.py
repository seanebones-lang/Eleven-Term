"""Tests for validation utilities"""
import pytest
from validation_utils import (
    validate_file_path, validate_command, validate_url,
    validate_tool_params, validate_config_value, sanitize_path,
    validate_json_structure
)

class TestValidationUtils:
    """Test validation utilities"""
    
    def test_validate_file_path(self):
        """Test file path validation"""
        # Valid path
        valid, error = validate_file_path("/tmp/test.txt", must_exist=False)
        assert valid
        
        # Path with traversal
        valid, error = validate_file_path("../../../etc/passwd")
        assert not valid
        assert "traversal" in error.lower()
    
    def test_validate_command(self):
        """Test command validation"""
        # Valid command
        valid, error = validate_command("ls -la")
        assert valid
        
        # Dangerous command
        valid, error = validate_command("rm -rf /")
        assert not valid
        assert "dangerous" in error.lower()
        
        # Too long
        valid, error = validate_command("a" * 20000)
        assert not valid
        assert "too long" in error.lower()
    
    def test_validate_url(self):
        """Test URL validation"""
        # Valid URL
        valid, error = validate_url("https://example.com")
        assert valid
        
        # Invalid URL
        valid, error = validate_url("not-a-url")
        assert not valid
        
        # Invalid scheme
        valid, error = validate_url("ftp://example.com")
        assert not valid
    
    def test_validate_tool_params(self):
        """Test tool parameter validation"""
        # Valid params
        valid, error = validate_tool_params(
            "test_tool",
            {"param1": "value1", "param2": 123},
            ["param1"],
            {"param2": int}
        )
        assert valid
        
        # Missing required param
        valid, error = validate_tool_params(
            "test_tool",
            {},
            ["param1"],
            {}
        )
        assert not valid
        assert "missing" in error.lower()
        
        # Wrong type
        valid, error = validate_tool_params(
            "test_tool",
            {"param1": 123},
            [],
            {"param1": str}
        )
        assert not valid
        assert "type" in error.lower()
    
    def test_validate_config_value(self):
        """Test config value validation"""
        # Valid temperature
        valid, error = validate_config_value("temperature", 0.5)
        assert valid
        
        # Invalid temperature
        valid, error = validate_config_value("temperature", 3.0)
        assert not valid
        
        # Valid max_tokens
        valid, error = validate_config_value("max_tokens", 1000)
        assert valid
        
        # Invalid max_tokens
        valid, error = validate_config_value("max_tokens", -1)
        assert not valid
    
    def test_sanitize_path(self):
        """Test path sanitization"""
        # Remove null bytes
        sanitized = sanitize_path("test\x00path")
        assert "\x00" not in sanitized
    
    def test_validate_json_structure(self):
        """Test JSON structure validation"""
        # Valid dict
        valid, error = validate_json_structure({"key": "value"}, dict, ["key"])
        assert valid
        
        # Missing key
        valid, error = validate_json_structure({}, dict, ["key"])
        assert not valid
        
        # Wrong type
        valid, error = validate_json_structure([], dict)
        assert not valid