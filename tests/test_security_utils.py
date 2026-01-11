#!/usr/bin/env python3
"""
Security utilities tests
"""

import pytest
import subprocess
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from security_utils import (
    sanitize_input,
    sanitize_command,
    validate_command_structure,
    execute_command_safely,
    SecurityError,
    MAX_COMMAND_LENGTH,
)


class TestSanitizeInput:
    """Test input sanitization"""
    
    def test_sanitize_normal_input(self):
        """Test sanitization of normal input"""
        result = sanitize_input("ls -la")
        assert result == "ls -la"
    
    def test_sanitize_removes_null_bytes(self):
        """Test that null bytes are removed"""
        result = sanitize_input("ls\x00-la")
        assert '\x00' not in result
        assert result == "ls-la"
    
    def test_sanitize_removes_control_chars(self):
        """Test that control characters are removed"""
        result = sanitize_input("ls\x01\x02-la")
        assert result == "ls-la"
    
    def test_sanitize_preserves_newline_tab(self):
        """Test that newline and tab are preserved"""
        result = sanitize_input("ls\n-la\t")
        assert '\n' in result
        assert '\t' in result
    
    def test_sanitize_max_length(self):
        """Test that max length is enforced"""
        long_input = "a" * (MAX_COMMAND_LENGTH + 1)
        with pytest.raises(SecurityError):
            sanitize_input(long_input)
    
    def test_sanitize_non_string(self):
        """Test that non-string input raises error"""
        with pytest.raises(SecurityError):
            sanitize_input(123)
        with pytest.raises(SecurityError):
            sanitize_input(None)


class TestSanitizeCommand:
    """Test command sanitization"""
    
    def test_sanitize_normal_command(self):
        """Test sanitization of normal command"""
        result = sanitize_command("ls -la")
        assert result == "ls -la"
    
    def test_sanitize_trims_whitespace(self):
        """Test that whitespace is trimmed"""
        result = sanitize_command("  ls -la  ")
        assert result == "ls -la"
    
    def test_sanitize_removes_null_bytes(self):
        """Test that null bytes are removed from commands"""
        result = sanitize_command("ls\x00-la")
        assert '\x00' not in result


class TestValidateCommandStructure:
    """Test command structure validation"""
    
    def test_validate_safe_command(self):
        """Test validation of safe command"""
        is_valid, error = validate_command_structure("ls -la")
        assert is_valid is True
        assert error is None
    
    def test_validate_dangerous_command_without_force(self):
        """Test that dangerous commands are rejected without force"""
        is_valid, error = validate_command_structure("rm -rf /tmp")
        assert is_valid is False
        assert "Dangerous" in error.lower() or "rm" in error.lower()
    
    def test_validate_dangerous_command_with_force(self):
        """Test that dangerous commands are allowed with force"""
        is_valid, error = validate_command_structure("rm -rf /tmp", allow_force=True)
        assert is_valid is True
        assert error is None
    
    def test_validate_empty_command(self):
        """Test that empty commands are rejected"""
        is_valid, error = validate_command_structure("")
        assert is_valid is False
        assert "empty" in error.lower()
    
    def test_validate_too_long_command(self):
        """Test that too long commands are rejected"""
        long_cmd = "a" * (MAX_COMMAND_LENGTH + 1)
        is_valid, error = validate_command_structure(long_cmd)
        assert is_valid is False
        assert "too long" in error.lower()
    
    def test_validate_injection_patterns(self):
        """Test that command injection patterns are detected"""
        injection_attempts = [
            "; rm -rf /",
            "&& rm -rf /",
            "| rm -rf /",
            "`rm -rf /`",
            "$(rm -rf /)",
            "${rm -rf /}",
        ]
        
        for cmd in injection_attempts:
            is_valid, error = validate_command_structure(cmd)
            assert is_valid is False, f"Injection pattern not detected: {cmd}"
            assert "injection" in error.lower() or "dangerous" in error.lower()


class TestExecuteCommandSafely:
    """Test safe command execution"""
    
    def test_execute_safe_command(self):
        """Test execution of safe command"""
        result = execute_command_safely("echo 'test'", allow_force=False, timeout=5)
        assert result.returncode == 0
        assert "test" in result.stdout
    
    def test_execute_dangerous_command_without_force(self):
        """Test that dangerous commands are blocked without force"""
        with pytest.raises(SecurityError):
            execute_command_safely("rm -rf /tmp/test", allow_force=False, timeout=5)
    
    def test_execute_dangerous_command_with_force(self):
        """Test that dangerous commands work with force (but still block system paths)"""
        # Even with force, we shouldn't allow system-destructive commands like "rm -rf /"
        with pytest.raises(SecurityError, match="System-destructive"):
            execute_command_safely("rm -rf /", allow_force=True, timeout=5)
    
    def test_execute_empty_command(self):
        """Test that empty commands are rejected"""
        with pytest.raises(SecurityError):
            execute_command_safely("", allow_force=False, timeout=5)
    
    def test_execute_invalid_command(self):
        """Test execution of invalid command"""
        # Invalid command (FileNotFoundError) should return error result, not raise SecurityError
        result = execute_command_safely("nonexistent_command_xyz123", allow_force=False, timeout=5)
        assert result.returncode != 0
        assert result.returncode == 127  # Command not found exit code
    
    def test_execute_timeout(self):
        """Test that commands timeout correctly"""
        # This test might take time - consider mocking
        # For now, test with a command that should timeout
        with pytest.raises(subprocess.TimeoutExpired):
            execute_command_safely("sleep 10", allow_force=False, timeout=1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
