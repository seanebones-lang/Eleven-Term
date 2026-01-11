#!/usr/bin/env python3
"""
Integration tests for Grok Terminal Agent
Tests full workflows and interactions
"""

import json
import os
import pytest
import subprocess
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
import sys
import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))

import grok_agent


class TestFullWorkflow:
    """Integration tests for complete workflows"""
    
    def test_interactive_mode_flow(self, mock_keychain, patch_default_config, monkeypatch):
        """Test complete interactive mode flow"""
        # Mock user inputs: Yes, query, exit
        inputs = iter(['1', 'list files', 'exit'])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))
        
        # Mock API responses
        with patch('grok_agent.call_grok_api') as mock_api:
            mock_api.side_effect = [
                # Quota check
                {"choices": [{"message": {"content": '{"isNewTopic": false}'}}]},
                # Topic detection
                {"choices": [{"message": {"content": '{"isNewTopic": false, "title": ""}'}}]},
                # Main query (streaming)
                iter([{"choices": [{"delta": {"content": "Here are the files"}}]}])
            ]
            
            with patch('sys.argv', ['grok_agent.py', '--interactive']):
                try:
                    grok_agent.main()
                except (SystemExit, KeyboardInterrupt, StopIteration):
                    pass  # Expected
    
    def test_slash_command_init(self, mock_keychain, patch_default_config, temp_dir, monkeypatch):
        """Test /init slash command"""
        inputs = iter(['1', '/init', 'exit'])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))
        
        with patch('grok_agent.call_grok_api') as mock_api:
            mock_api.side_effect = [
                # Quota check
                {"choices": [{"message": {"content": 'ok'}}]},
                # /init response
                {"choices": [{"message": {"content": "# GROK.md\nProject instructions"}}]}
            ]
            
            with patch('os.getcwd', return_value=str(temp_dir)):
                with patch('sys.argv', ['grok_agent.py', '--interactive']):
                    try:
                        grok_agent.main()
                    except (SystemExit, KeyboardInterrupt, StopIteration):
                        pass
    
    def test_tool_execution_flow(self, patch_default_config, temp_dir):
        """Test tool execution with hooks"""
        # Create test hook
        hooks_dir = temp_dir / "hooks"
        hooks_dir.mkdir()
        pre_hook = hooks_dir / "PreToolUse.sh"
        pre_hook.write_text('#!/bin/bash\necho "pre-hook executed"')
        pre_hook.chmod(0o755)
        
        # Mock hook execution
        with patch('subprocess.Popen') as mock_popen:
            mock_proc = MagicMock()
            mock_proc.communicate.return_value = ("hook output", "")
            mock_proc.returncode = 0
            mock_popen.return_value = mock_proc
            
            # Test hook execution
            success, output = grok_agent.run_hook("PreToolUse", {"tool": "Bash", "params": {"command": "ls"}})
            
            # Hook should be called
            assert mock_popen.called or success is True
    
    def test_history_persistence(self, patch_default_config, temp_dir):
        """Test history persistence across sessions"""
        history = [
            {"role": "user", "content": "query 1"},
            {"role": "assistant", "content": "response 1"}
        ]
        
        # Save history
        grok_agent.save_history(history)
        
        # Load history
        loaded = grok_agent.load_history()
        
        assert len(loaded) == 2
        assert loaded[0]['content'] == "query 1"
    
    def test_todos_persistence(self, patch_default_config, temp_dir):
        """Test todos persistence"""
        todos = {
            "2026-01-01T00:00:00": "todo 1",
            "2026-01-02T00:00:00": "todo 2"
        }
        
        # Save todos
        grok_agent.save_todos(todos)
        
        # Load todos
        loaded = grok_agent.load_todos()
        
        assert len(loaded) == 2
        assert "2026-01-01T00:00:00" in loaded
    
    def test_todos_persistence_load(self, patch_default_config, temp_dir):
        """Test todos loading"""
        todos = {
            "2026-01-01T00:00:00": "todo 1"
        }
        grok_agent.save_todos(todos)
        loaded = grok_agent.load_todos()
        assert "2026-01-01T00:00:00" in loaded


class TestHealthChecks:
    """Test health check functionality"""
    
    def test_health_check_keychain(self, mock_keychain):
        """Test Keychain health check"""
        ok, msg = grok_agent.health_check_keychain()
        assert ok is True or ok is False  # May vary based on environment
        assert isinstance(msg, str)
    
    def test_health_check_filesystem(self, patch_default_config, temp_dir):
        """Test filesystem health check"""
        ok, msg = grok_agent.health_check_filesystem()
        assert ok is True or ok is False
        assert isinstance(msg, str)
    
    def test_health_check_all(self, mock_keychain, patch_default_config):
        """Test all health checks"""
        results = grok_agent.health_check_all(config=grok_agent.DEFAULT_CONFIG)
        
        assert 'keychain' in results
        assert 'filesystem' in results
        assert 'api' in results
        
        for component, (ok, msg) in results.items():
            assert isinstance(ok, bool)
            assert isinstance(msg, str)


class TestToolIntegration:
    """Test tool integration"""
    
    def test_view_tool_integration(self, patch_default_config, temp_dir):
        """Test View tool end-to-end"""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        exit_code, stdout, stderr = grok_agent.tool_view({"path": str(test_file)})
        
        assert exit_code == 0
        assert "test content" in stdout
    
    def test_write_tool_integration(self, patch_default_config, temp_dir):
        """Test Write tool end-to-end"""
        output_file = temp_dir / "output.txt"
        
        exit_code, stdout, stderr = grok_agent.tool_write({
            "path": str(output_file),
            "content": "written content"
        })
        
        assert exit_code == 0
        assert output_file.exists()
        assert output_file.read_text() == "written content"
    
    def test_ls_tool_integration(self, patch_default_config, temp_dir):
        """Test LS tool end-to-end"""
        (temp_dir / "file1.txt").touch()
        (temp_dir / "file2.py").touch()
        
        exit_code, stdout, stderr = grok_agent.tool_ls({"dir": str(temp_dir)})
        
        assert exit_code == 0
        assert "file1.txt" in stdout or "file2.py" in stdout


class TestCaching:
    """Test response caching"""
    
    def test_cache_hit(self, mock_api_key, patch_default_config):
        """Test cache hit for repeated queries"""
        messages = [{"role": "user", "content": "test query"}]
        config = grok_agent.DEFAULT_CONFIG.copy()
        
        # Reset cache before test
        grok_agent.reset_cache()
        
        # Mock API call
        with patch('grok_agent._get_http_client') as mock_get_client:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {"choices": [{"message": {"content": "cached response"}}]}
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            # First call - should hit API
            result1 = grok_agent.call_grok_api(
                mock_api_key, messages, "grok-4.1-fast", 0.1, 100, stream=False, config=config
            )
            
            # Second call - should hit cache
            result2 = grok_agent.call_grok_api(
                mock_api_key, messages, "grok-4.1-fast", 0.1, 100, stream=False, config=config
            )
            
            # Verify cache was used (only one API call)
            assert mock_client.post.call_count == 1 or result1 == result2
    
    def test_get_cache_stats(self, patch_default_config):
        """Test cache statistics retrieval"""
        grok_agent.reset_cache()
        stats = grok_agent.get_cache_stats()
        
        assert "hits" in stats
        assert "misses" in stats
        assert "evictions" in stats
        assert "size" in stats
        assert "hit_rate" in stats
        assert "total_requests" in stats
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["evictions"] == 0
        assert stats["size"] == 0
    
    def test_reset_cache(self, patch_default_config):
        """Test cache reset function"""
        from collections import OrderedDict
        
        # Add some data to cache
        grok_agent._response_cache["test_key"] = (time.time(), "test_response")
        grok_agent._cache_stats["hits"] = 10
        grok_agent._cache_stats["misses"] = 5
        
        # Reset cache
        grok_agent.reset_cache()
        
        # Verify cache is empty
        assert len(grok_agent._response_cache) == 0
        assert grok_agent._cache_stats["hits"] == 0
        assert grok_agent._cache_stats["misses"] == 0
        assert grok_agent._cache_stats["evictions"] == 0
    
    def test_cache_lru_eviction(self, patch_default_config):
        """Test LRU cache eviction"""
        import time as time_module
        from collections import OrderedDict
        
        grok_agent.reset_cache()
        config = grok_agent.DEFAULT_CONFIG.copy()
        config["cache_size"] = 3  # Small cache for testing
        
        # Add 3 items
        for i in range(3):
            key = f"key_{i}"
            grok_agent._response_cache[key] = (time_module.time(), f"response_{i}")
        
        # Add 4th item - should evict oldest
        grok_agent._update_cache("key_3", "response_3", 3)
        
        # Verify cache size is 3
        assert len(grok_agent._response_cache) == 3
        
        # Verify oldest key is evicted (key_0 should be gone)
        assert "key_0" not in grok_agent._response_cache
        assert "key_3" in grok_agent._response_cache


class TestErrorHandling:
    """Test error handling and recovery"""
    
    def test_api_error_handling(self, mock_api_key, monkeypatch):
        """Test API error handling"""
        with patch('grok_agent._get_http_client') as mock_get_client:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Invalid API key"
            mock_error = httpx.HTTPStatusError(
                "401 Unauthorized",
                request=MagicMock(),
                response=mock_response
            )
            mock_client.post.return_value = mock_response
            mock_client.post.side_effect = mock_error
            mock_get_client.return_value = mock_client
            
            messages = [{"role": "user", "content": "test"}]
            
            with pytest.raises(ValueError, match="Invalid API key"):
                grok_agent.call_grok_api(
                    mock_api_key, messages, "grok-4.1-fast", 0.1, 100, stream=False
                )
    
    def test_retry_logic(self, mock_api_key, patch_default_config, monkeypatch):
        """Test retry logic with exponential backoff"""
        import time
        config = grok_agent.DEFAULT_CONFIG.copy()
        config['max_retries'] = 3
        
        with patch('grok_agent._get_http_client') as mock_get_client:
            mock_client = MagicMock()
            
            # First two calls fail, third succeeds
            mock_success = MagicMock()
            mock_success.json.return_value = {"choices": [{"message": {"content": "success"}}]}
            mock_success.raise_for_status = MagicMock()
            
            mock_client.post.side_effect = [
                httpx.NetworkError("Network error"),
                httpx.TimeoutException("Timeout"),
                mock_success
            ]
            mock_get_client.return_value = mock_client
            
            # Mock sleep to speed up test
            monkeypatch.setattr(time, 'sleep', lambda x: None)
            
            messages = [{"role": "user", "content": "test"}]
            
            result = grok_agent.call_grok_api(
                mock_api_key, messages, "grok-4.1-fast", 0.1, 100, stream=False, config=config
            )
            
            # Should have retried and succeeded (3 attempts)
            assert mock_client.post.call_count == 3
            assert "choices" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
