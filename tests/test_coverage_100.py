#!/usr/bin/env python3
"""
Additional tests to reach 100% coverage
Tests for missing coverage areas
"""

import json
import os
import pytest
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
import sys
import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))

import grok_agent


class TestFallbackColored:
    """Test fallback colored function when termcolor not available"""
    
    def test_colored_fallback(self, monkeypatch):
        """Test colored function when termcolor import fails"""
        # Mock ImportError for termcolor
        import builtins
        original_import = builtins.__import__
        
        def mock_import(name, *args, **kwargs):
            if name == 'termcolor':
                raise ImportError("No module named 'termcolor'")
            return original_import(name, *args, **kwargs)
        
        monkeypatch.setattr(builtins, '__import__', mock_import)
        
        # Reload module to trigger fallback
        import importlib
        importlib.reload(grok_agent)
        
        # Test colored function
        result = grok_agent.colored("test", "red")
        assert isinstance(result, str)
        assert "test" in result
        
        # Restore original
        importlib.reload(grok_agent)


class TestFallbackSecurityUtils:
    """Test fallback security utils when import fails"""
    
    def test_fallback_security_utils(self, monkeypatch):
        """Test fallback security utils when security_utils import fails"""
        import builtins
        original_import = builtins.__import__
        
        def mock_import(name, *args, **kwargs):
            if name == 'security_utils':
                raise ImportError("No module named 'security_utils'")
            return original_import(name, *args, **kwargs)
        
        monkeypatch.setattr(builtins, '__import__', mock_import)
        
        # Reload module to trigger fallback
        import importlib
        importlib.reload(grok_agent)
        
        # Test fallback functions exist
        assert hasattr(grok_agent, 'sanitize_input')
        assert hasattr(grok_agent, 'sanitize_command')
        assert hasattr(grok_agent, 'SecurityError')
        assert hasattr(grok_agent, 'execute_command_safely')
        
        # Restore original
        importlib.reload(grok_agent)


class TestToolErrors:
    """Test tool function error cases"""
    
    def test_tool_view_error_reading(self, temp_dir, monkeypatch):
        """Test tool_view error when reading file"""
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")
        
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            exit_code, stdout, stderr = grok_agent.tool_view({"path": str(test_file)})
            assert exit_code == 1
            assert "Permission denied" in stderr
    
    def test_tool_edit_exception(self, temp_dir):
        """Test tool_edit with exception"""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test")
        
        with patch('subprocess.run', side_effect=Exception("vim not found")):
            exit_code, stdout, stderr = grok_agent.tool_edit({"path": str(test_file)})
            assert exit_code == 1
            assert "vim not found" in stderr
    
    def test_tool_write_exception(self, temp_dir):
        """Test tool_write with exception"""
        with patch('builtins.open', side_effect=IOError("Disk full")):
            exit_code, stdout, stderr = grok_agent.tool_write({
                "path": str(temp_dir / "test.txt"),
                "content": "test"
            })
            assert exit_code == 1
            assert "Disk full" in stderr
    
    def test_tool_write_no_path(self):
        """Test tool_write with no path"""
        exit_code, stdout, stderr = grok_agent.tool_write({"content": "test"})
        assert exit_code == 1
        assert "No path provided" in stderr
    
    def test_tool_ls_exception(self):
        """Test tool_ls with exception"""
        with patch('os.listdir', side_effect=PermissionError("Access denied")):
            exit_code, stdout, stderr = grok_agent.tool_ls({"dir": "/"})
            assert exit_code == 1
            assert "Access denied" in stderr
    
    def test_tool_glob_exception(self):
        """Test tool_glob with exception"""
        with patch('glob.glob', side_effect=Exception("Pattern error")):
            exit_code, stdout, stderr = grok_agent.tool_glob({"pattern": "**/*.py"})
            assert exit_code == 1
            assert "Pattern error" in stderr
    
    def test_tool_grep_exception(self, temp_dir):
        """Test tool_grep with exception"""
        with patch('subprocess.run', side_effect=Exception("grep error")):
            exit_code, stdout, stderr = grok_agent.tool_grep({
                "query": "test",
                "dir": str(temp_dir)
            })
            assert exit_code == 1
            assert "grep error" in stderr


class TestConfigValidation:
    """Test config loading validation edge cases"""
    
    def test_load_config_invalid_temperature(self, temp_dir, monkeypatch):
        """Test config with invalid temperature"""
        config_file = temp_dir / ".grok_terminal_config.json"
        config_file.write_text('{"temperature": 3.0}')  # Invalid (>2)
        
        original_expanduser = os.path.expanduser
        def mock_expanduser(path):
            if 'grok_terminal_config' in path:
                return str(config_file)
            return original_expanduser(path)
        monkeypatch.setattr(os.path, "expanduser", mock_expanduser)
        
        config = grok_agent.load_config()
        # Should use default (0.1) instead of invalid 3.0
        assert config['temperature'] == 0.1
    
    def test_load_config_invalid_max_tokens(self, temp_dir, monkeypatch):
        """Test config with invalid max_tokens"""
        config_file = temp_dir / ".grok_terminal_config.json"
        config_file.write_text('{"max_tokens": 200000}')  # Invalid (>100000)
        
        original_expanduser = os.path.expanduser
        def mock_expanduser(path):
            if 'grok_terminal_config' in path:
                return str(config_file)
            return original_expanduser(path)
        monkeypatch.setattr(os.path, "expanduser", mock_expanduser)
        
        config = grok_agent.load_config()
        # Should use default (2048) instead of invalid 200000
        assert config['max_tokens'] == 2048
    
    def test_load_config_invalid_cache_size(self, temp_dir, monkeypatch):
        """Test config with invalid cache_size"""
        config_file = temp_dir / ".grok_terminal_config.json"
        config_file.write_text('{"cache_size": -1}')  # Invalid (<=0)
        
        original_expanduser = os.path.expanduser
        def mock_expanduser(path):
            if 'grok_terminal_config' in path:
                return str(config_file)
            return original_expanduser(path)
        monkeypatch.setattr(os.path, "expanduser", mock_expanduser)
        
        config = grok_agent.load_config()
        # Should use default instead of invalid -1
        assert config['cache_size'] == grok_agent.CACHE_DEFAULT_SIZE
    
    def test_load_config_invalid_model(self, temp_dir, monkeypatch):
        """Test config with invalid model (non-string)"""
        config_file = temp_dir / ".grok_terminal_config.json"
        config_file.write_text('{"model": 123}')  # Invalid (not string)
        
        original_expanduser = os.path.expanduser
        def mock_expanduser(path):
            if 'grok_terminal_config' in path:
                return str(config_file)
            return original_expanduser(path)
        monkeypatch.setattr(os.path, "expanduser", mock_expanduser)
        
        config = grok_agent.load_config()
        # Should use default instead of invalid 123
        assert config['model'] == grok_agent.DEFAULT_CONFIG['model']
    
    def test_load_config_invalid_boolean(self, temp_dir, monkeypatch):
        """Test config with invalid boolean"""
        config_file = temp_dir / ".grok_terminal_config.json"
        config_file.write_text('{"auto_log": "yes"}')  # Invalid (not bool)
        
        original_expanduser = os.path.expanduser
        def mock_expanduser(path):
            if 'grok_terminal_config' in path:
                return str(config_file)
            return original_expanduser(path)
        monkeypatch.setattr(os.path, "expanduser", mock_expanduser)
        
        config = grok_agent.load_config()
        # Should use default instead of invalid "yes"
        assert config['auto_log'] == grok_agent.DEFAULT_CONFIG['auto_log']


class TestHistoryErrors:
    """Test history loading/saving error cases"""
    
    def test_load_history_file_lock_error(self, temp_dir, monkeypatch):
        """Test load_history with file lock error"""
        history_file = temp_dir / ".grok_terminal_history.json"
        history_file.write_text('[]')
        
        original_expanduser = os.path.expanduser
        def mock_expanduser(path):
            if 'history' in path.lower():
                return str(history_file)
            return original_expanduser(path)
        monkeypatch.setattr(os.path, "expanduser", mock_expanduser)
        
        # Mock fcntl.flock to raise error
        with patch('fcntl.flock', side_effect=IOError("Lock failed")):
            history = grok_agent.load_history()
            # Should continue without lock
            assert isinstance(history, list)
    
    def test_load_history_invalid_role(self, temp_dir, monkeypatch):
        """Test load_history with invalid role"""
        history_file = temp_dir / ".grok_terminal_history.json"
        history_file.write_text('[{"role": "invalid", "content": "test"}]')
        
        original_expanduser = os.path.expanduser
        def mock_expanduser(path):
            if 'history' in path.lower():
                return str(history_file)
            return original_expanduser(path)
        monkeypatch.setattr(os.path, "expanduser", mock_expanduser)
        
        history = grok_agent.load_history()
        # Invalid role should be filtered out
        assert len(history) == 0
    
    def test_save_history_lock_error(self, temp_dir, monkeypatch):
        """Test save_history with file lock error"""
        history_file = temp_dir / ".grok_terminal_history.json"
        
        original_expanduser = os.path.expanduser
        def mock_expanduser(path):
            if 'history' in path.lower():
                return str(history_file)
            return original_expanduser(path)
        monkeypatch.setattr(os.path, "expanduser", mock_expanduser)
        
        # Mock fcntl.flock to raise error
        with patch('fcntl.flock', side_effect=IOError("Lock failed")):
            grok_agent.save_history([{"role": "user", "content": "test"}])
            # Should continue without lock


class TestCallGrokApiErrors:
    """Test call_grok_api error cases"""
    
    def test_call_grok_api_401_error(self, mock_api_key):
        """Test call_grok_api with 401 error"""
        with patch('grok_agent._get_http_client') as mock_get_client:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_error = httpx.HTTPStatusError("Unauthorized", request=MagicMock(), response=mock_response)
            mock_client.post.side_effect = mock_error
            mock_get_client.return_value = mock_client
            
            with pytest.raises(ValueError, match="Invalid API key"):
                grok_agent.call_grok_api(
                    mock_api_key, [{"role": "user", "content": "test"}],
                    "grok-4.1-fast", 0.1, 2048, stream=False
                )
    
    def test_call_grok_api_429_error(self, mock_api_key):
        """Test call_grok_api with 429 error"""
        with patch('grok_agent._get_http_client') as mock_get_client:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.text = "Rate limit"
            mock_error = httpx.HTTPStatusError("Rate limit", request=MagicMock(), response=mock_response)
            mock_client.post.side_effect = mock_error
            mock_get_client.return_value = mock_client
            
            with pytest.raises(ValueError, match="Rate limit exceeded"):
                grok_agent.call_grok_api(
                    mock_api_key, [{"role": "user", "content": "test"}],
                    "grok-4.1-fast", 0.1, 2048, stream=False
                )
    
    def test_call_grok_api_grokcode_message_format(self, mock_api_key):
        """Test call_grok_api with Grok-Code message format"""
        config = grok_agent.DEFAULT_CONFIG.copy()
        config['api_endpoint'] = 'https://grokcode.vercel.app/api/chat'
        
        with patch('grok_agent._get_http_client') as mock_get_client:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {"content": "test response"}
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            result = grok_agent.call_grok_api(
                mock_api_key,
                [{"role": "assistant", "content": "prev"}, {"role": "user", "content": "test"}],
                "grok-4.1-fast", 0.1, 2048, stream=False, config=config
            )
            
            assert "choices" in result
            assert result["choices"][0]["message"]["content"] == "test response"


class TestRunHookErrors:
    """Test hook execution error cases"""
    
    def test_run_hook_timeout(self, patch_default_config, temp_dir):
        """Test run_hook with timeout"""
        hooks_dir = temp_dir / "hooks"
        hooks_dir.mkdir()
        hook_file = hooks_dir / "PreToolUse.sh"
        hook_file.write_text('#!/bin/bash\nsleep 60')
        hook_file.chmod(0o755)
        
        with patch('subprocess.Popen') as mock_popen:
            mock_proc = MagicMock()
            mock_proc.communicate.side_effect = subprocess.TimeoutExpired("bash", 30)
            mock_popen.return_value = mock_proc
            
            success, output = grok_agent.run_hook("PreToolUse", {"tool": "Bash"})
            assert success is False
            assert "timeout" in output.lower()
    
    def test_run_hook_exception(self, patch_default_config, temp_dir):
        """Test run_hook with exception"""
        hooks_dir = temp_dir / "hooks"
        hooks_dir.mkdir()
        hook_file = hooks_dir / "PreToolUse.sh"
        hook_file.write_text('#!/bin/bash\necho test')
        hook_file.chmod(0o755)
        
        with patch('subprocess.Popen', side_effect=Exception("Process error")):
            success, output = grok_agent.run_hook("PreToolUse", {"tool": "Bash"})
            assert success is False
            assert "Process error" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
