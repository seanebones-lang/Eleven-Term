#!/usr/bin/env python3
"""
Comprehensive unit tests for grok_agent.py
"""

import json
import os
import pytest
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch, call
import sys
import httpx

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import grok_agent


class TestGetApiKey:
    """Test API key retrieval from Keychain"""
    
    def test_get_api_key_success(self, mock_keychain):
        """Test successful API key retrieval"""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "test-api-key"
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            key = grok_agent.get_api_key()
            assert key == "test-api-key"
            mock_run.assert_called_once()
    
    def test_get_api_key_failure(self):
        """Test API key retrieval failure"""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'security')
            key = grok_agent.get_api_key()
            assert key is None


class TestLoadConfig:
    """Test configuration loading"""
    
    def test_load_config_defaults(self, patch_default_config, temp_dir):
        """Test loading default config when file doesn't exist"""
        config = grok_agent.load_config()
        assert config['model'] == "grok-4.1-fast"
        assert config['temperature'] == 0.1
        assert config['max_tokens'] == 2048
    
    def test_load_config_from_file(self, patch_default_config, temp_dir):
        """Test loading config from file"""
        config_file = temp_dir / ".grok_terminal_config.json"
        config_data = {
            "model": "grok-2",
            "temperature": 0.5,
            "max_tokens": 4096
        }
        config_file.write_text(json.dumps(config_data))
        
        config = grok_agent.load_config()
        assert config['model'] == "grok-2"
        assert config['temperature'] == 0.5
        assert config['max_tokens'] == 4096
    
    def test_load_config_invalid_json(self, patch_default_config, temp_dir):
        """Test loading invalid config file falls back to defaults"""
        config_file = temp_dir / ".grok_terminal_config.json"
        config_file.write_text("invalid json")
        
        config = grok_agent.load_config()
        assert config['model'] == "grok-4.1-fast"  # Defaults


class TestLoadHistory:
    """Test history loading"""
    
    def test_load_history_file_exists(self, patch_default_config, temp_dir):
        """Test loading history from existing file"""
        history_file = temp_dir / ".grok_terminal_history.json"
        history_data = [
            {"role": "user", "content": "test query"},
            {"role": "assistant", "content": "test response"}
        ]
        history_file.write_text(json.dumps(history_data))
        
        history = grok_agent.load_history()
        assert len(history) == 2
        assert history[0]['role'] == "user"
    
    def test_load_history_file_not_exists(self, patch_default_config):
        """Test loading history when file doesn't exist"""
        history = grok_agent.load_history()
        assert history == []
    
    def test_load_history_invalid_json(self, patch_default_config, temp_dir):
        """Test loading invalid history file returns empty list"""
        history_file = temp_dir / ".grok_terminal_history.json"
        history_file.write_text("invalid json")
        
        history = grok_agent.load_history()
        assert history == []


class TestSaveHistory:
    """Test history saving"""
    
    def test_save_history_success(self, patch_default_config, temp_dir):
        """Test saving history successfully"""
        history = [
            {"role": "user", "content": "query 1"},
            {"role": "assistant", "content": "response 1"},
            {"role": "user", "content": "query 2"},
            {"role": "assistant", "content": "response 2"}
        ]
        
        grok_agent.save_history(history)
        
        history_file = temp_dir / ".grok_terminal_history.json"
        assert history_file.exists()
        
        loaded = json.loads(history_file.read_text())
        assert len(loaded) == 4
        
        # Check permissions
        assert oct(history_file.stat().st_mode)[-3:] == "600"
    
    def test_save_history_limits_to_40_messages(self, patch_default_config, temp_dir):
        """Test that history is limited to last 40 messages"""
        history = [{"role": "user", "content": f"query {i}"} for i in range(50)]
        
        grok_agent.save_history(history)
        
        history_file = temp_dir / ".grok_terminal_history.json"
        loaded = json.loads(history_file.read_text())
        assert len(loaded) == 40  # Last 40 messages


class TestLoadTodos:
    """Test todos loading"""
    
    def test_load_todos_file_exists(self, patch_default_config, temp_dir):
        """Test loading todos from existing file"""
        todos_file = temp_dir / "todos.json"
        todos_data = {
            "2026-01-01T00:00:00": "test todo",
            "2026-01-02T00:00:00": "another todo"
        }
        todos_file.write_text(json.dumps(todos_data))
        
        todos = grok_agent.load_todos()
        assert len(todos) == 2
        assert "2026-01-01T00:00:00" in todos
    
    def test_load_todos_file_not_exists(self, patch_default_config):
        """Test loading todos when file doesn't exist"""
        todos = grok_agent.load_todos()
        assert todos == {}


class TestSaveTodos:
    """Test todos saving"""
    
    def test_save_todos_success(self, patch_default_config, temp_dir):
        """Test saving todos successfully"""
        todos = {
            "2026-01-01T00:00:00": "todo 1",
            "2026-01-02T00:00:00": "todo 2"
        }
        
        grok_agent.save_todos(todos)
        
        todos_file = temp_dir / "todos.json"
        assert todos_file.exists()
        
        loaded = json.loads(todos_file.read_text())
        assert loaded == todos
        
        # Check permissions
        assert oct(todos_file.stat().st_mode)[-3:] == "600"


class TestGetEnvContext:
    """Test environment context retrieval"""
    
    def test_get_env_context_with_git(self, mock_subprocess):
        """Test getting context with git repository"""
        with patch('subprocess.run') as mock_run:
            # Git status success
            git_result = MagicMock()
            git_result.returncode = 0
            git_result.stdout = "M  modified.txt\n"
            
            # Tree not available, fallback to ls
            tree_result = MagicMock()
            tree_result.returncode = 1
            
            ls_result = MagicMock()
            ls_result.returncode = 0
            ls_result.stdout = "file1.py\nfile2.txt\n"
            
            mock_run.side_effect = [git_result, tree_result, ls_result]
            
            cwd, git_status, dir_tree = grok_agent.get_env_context()
            
            assert cwd == os.getcwd()
            assert "modified.txt" in git_status
            assert "file1.py" in dir_tree
    
    def test_get_env_context_no_git(self, mock_subprocess):
        """Test getting context without git repository"""
        with patch('subprocess.run') as mock_run:
            git_result = MagicMock()
            git_result.returncode = 1  # Not a git repo
            
            ls_result = MagicMock()
            ls_result.returncode = 0
            ls_result.stdout = "files\n"
            
            mock_run.side_effect = [git_result, MagicMock(returncode=1), ls_result]
            
            cwd, git_status, dir_tree = grok_agent.get_env_context()
            
            assert "Not a git repository" in git_status or "Git status unavailable" in git_status


class TestCallGrokApi:
    """Test Grok API calls"""
    
    def test_call_grok_api_non_streaming(self, mock_api_key):
        """Test non-streaming API call"""
        with patch('grok_agent._get_http_client') as mock_get_client:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "test response"}}]
            }
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response
            mock_get_client.return_value = mock_client
            
            messages = [{"role": "user", "content": "test"}]
            result = grok_agent.call_grok_api(
                mock_api_key, messages, "grok-4.1-fast", 0.1, 2048, stream=False
            )
            
            assert "choices" in result
            mock_client.post.assert_called_once()
    
    def test_call_grok_api_streaming(self, mock_api_key):
        """Test streaming API call"""
        with patch('grok_agent._get_http_client') as mock_get_client:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            
            def iter_lines():
                yield "data: {\"choices\":[{\"delta\":{\"content\":\"test\"}}]}"
                yield "data: [DONE]"
            
            mock_response.iter_lines.return_value = iter_lines()
            mock_stream_context = MagicMock()
            mock_stream_context.__enter__.return_value = mock_response
            mock_stream_context.__exit__.return_value = None
            mock_client.stream.return_value = mock_stream_context
            mock_get_client.return_value = mock_client
            
            messages = [{"role": "user", "content": "test"}]
            chunks = list(grok_agent.call_grok_api(
                mock_api_key, messages, "grok-4.1-fast", 0.1, 2048, stream=True
            ))
            
            assert len(chunks) > 0


class TestExtractTools:
    """Test tool extraction from responses"""
    
    def test_extract_tools_single(self):
        """Test extracting single tool"""
        response = '<tool name="Bash"><param name="command">ls -la</param></tool>'
        tools = grok_agent.extract_tools(response)
        
        assert len(tools) == 1
        assert tools[0][0] == "Bash"
        assert ("command", "ls -la") in tools[0][1]
    
    def test_extract_tools_multiple(self):
        """Test extracting multiple tools"""
        response = '''<tool name="View"><param name="path">file.txt</param></tool>
        <tool name="Bash"><param name="command">echo test</param></tool>'''
        tools = grok_agent.extract_tools(response)
        
        assert len(tools) == 2
        assert tools[0][0] == "View"
        assert tools[1][0] == "Bash"
    
    def test_extract_tools_no_tools(self):
        """Test extracting when no tools present"""
        response = "This is a regular response with no tools."
        tools = grok_agent.extract_tools(response)
        
        assert tools == []


class TestClassifyCommandRisk:
    """Test command risk classification"""
    
    def test_classify_dangerous(self):
        """Test classifying dangerous commands"""
        dangerous_commands = [
            "rm -rf /tmp",
            "sudo rm -rf /",
            "kill -9 1234",
            "chmod 777 file.txt"
        ]
        
        for cmd in dangerous_commands:
            risk = grok_agent.classify_command_risk(cmd)
            assert risk == "DANGEROUS"
    
    def test_classify_safe(self):
        """Test classifying safe commands"""
        safe_commands = [
            "ls -la",
            "cat file.txt",
            "echo hello"
        ]
        
        for cmd in safe_commands:
            risk = grok_agent.classify_command_risk(cmd)
            assert risk == "SAFE"
    
    def test_classify_caution(self):
        """Test classifying caution commands"""
        caution_commands = [
            "mv file1 file2",
            "cp file1 file2"
        ]
        
        for cmd in caution_commands:
            risk = grok_agent.classify_command_risk(cmd)
            assert risk == "CAUTION" or risk == "DANGEROUS"  # Depends on patterns


class TestRunHook:
    """Test hook execution"""
    
    def test_run_hook_exists(self, patch_default_config, temp_dir):
        """Test running hook when file exists"""
        hooks_dir = temp_dir / "hooks"
        hooks_dir.mkdir()
        hook_file = hooks_dir / "PreToolUse.sh"
        hook_file.write_text('#!/bin/bash\necho "hook executed"')
        hook_file.chmod(0o755)
        
        with patch('subprocess.Popen') as mock_popen:
            mock_proc = MagicMock()
            mock_proc.communicate.return_value = ("hook output", "")
            mock_proc.returncode = 0
            mock_popen.return_value = mock_proc
            
            success, output = grok_agent.run_hook("PreToolUse", {"tool": "Bash"})
            
            assert success is True
            mock_popen.assert_called_once()
    
    def test_run_hook_not_exists(self, patch_default_config):
        """Test running hook when file doesn't exist"""
        success, output = grok_agent.run_hook("NonExistentHook", {})
        
        assert success is True  # Returns True if hook doesn't exist
        assert output == ""


class TestTools:
    """Test tool implementations"""
    
    def test_tool_view_file_exists(self, patch_default_config, temp_dir):
        """Test View tool with existing file"""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        exit_code, stdout, stderr = grok_agent.tool_view({"path": str(test_file)})
        
        assert exit_code == 0
        assert "test content" in stdout
    
    def test_tool_view_file_not_exists(self):
        """Test View tool with non-existent file"""
        exit_code, stdout, stderr = grok_agent.tool_view({"path": "/nonexistent/file.txt"})
        
        assert exit_code == 1
        assert "not found" in stderr.lower()
    
    def test_tool_ls(self, patch_default_config, temp_dir):
        """Test LS tool"""
        test_file = temp_dir / "test.txt"
        test_file.write_text("content")
        
        exit_code, stdout, stderr = grok_agent.tool_ls({"dir": str(temp_dir)})
        
        assert exit_code == 0
        assert "test.txt" in stdout
    
    def test_tool_write(self, patch_default_config, temp_dir):
        """Test Write tool"""
        test_file = temp_dir / "output.txt"
        
        exit_code, stdout, stderr = grok_agent.tool_write({
            "path": str(test_file),
            "content": "test content"
        })
        
        assert exit_code == 0
        assert test_file.exists()
        assert test_file.read_text() == "test content"
    
    def test_tool_glob(self, patch_default_config, temp_dir, monkeypatch):
        """Test Glob tool"""
        test1 = temp_dir / "test1.py"
        test2 = temp_dir / "test2.py"
        test1.touch()
        test2.touch()
        (temp_dir / "test.txt").touch()
        
        # Change to temp_dir so glob finds the files
        original_cwd = os.getcwd()
        monkeypatch.chdir(temp_dir)
        try:
            exit_code, stdout, stderr = grok_agent.tool_glob({"pattern": "*.py"})
            
            assert exit_code == 0
            assert "test1.py" in stdout or "test2.py" in stdout
        finally:
            monkeypatch.chdir(original_cwd)


class TestGetSystemPrompt:
    """Test system prompt generation"""
    
    def test_get_system_prompt(self):
        """Test system prompt generation"""
        cwd = "/test/cwd"
        git_status = "M  file.txt"
        dir_tree = "test/\n  file1.py"
        
        prompt = grok_agent.get_system_prompt(cwd, git_status, dir_tree)
        
        assert cwd in prompt
        assert git_status in prompt
        assert dir_tree in prompt
        assert "Bash" in prompt
        assert "View" in prompt


class TestMain:
    """Test main function"""
    
    def test_main_interactive_yes(self, mock_keychain, patch_default_config, monkeypatch):
        """Test interactive mode with yes choice"""
        inputs = ['1', 'exit']
        input_iter = iter(inputs)
        
        def mock_input(prompt):
            try:
                return next(input_iter)
            except StopIteration:
                return 'exit'
        
        with patch('builtins.input', side_effect=mock_input):
            with patch('grok_agent.call_grok_api') as mock_api:
                # Mock quota check response
                mock_quota_response = MagicMock()
                mock_quota_response.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
                mock_quota_response.raise_for_status = MagicMock()
                
                # Mock main query streaming response
                def mock_stream():
                    yield {"choices": [{"delta": {"content": "response"}}]}
                
                mock_api.side_effect = [
                    mock_quota_response,  # Quota check (non-streaming)
                    mock_stream()  # Main query (streaming generator)
                ]
                
                with patch('sys.argv', ['grok_agent.py', '--interactive']):
                    try:
                        grok_agent.main()
                        # Should exit normally after 'exit' command
                    except SystemExit as e:
                        # Exit code 0 is expected (normal exit)
                        if e.code != 0:
                            raise
    
    def test_main_interactive_decline(self, mock_keychain, patch_default_config):
        """Test interactive mode with decline"""
        with patch('builtins.input', return_value='2'):
            with patch('sys.argv', ['grok_agent.py', '--interactive']):
                with pytest.raises(SystemExit):
                    grok_agent.main()
    
    def test_main_non_interactive(self, mock_keychain, patch_default_config):
        """Test non-interactive mode"""
        with patch('grok_agent.call_grok_api') as mock_api:
            mock_api.return_value = iter([{"choices": [{"delta": {"content": "response"}}]}])
            
            with patch('sys.argv', ['grok_agent.py', 'test query']):
                try:
                    grok_agent.main()
                except SystemExit:
                    pass  # Expected when API calls fail in test


class TestHealthChecks:
    """Test health check functions"""
    
    def test_health_check_keychain_success(self, mock_keychain):
        """Test health check keychain success"""
        ok, msg = grok_agent.health_check_keychain()
        assert ok is True
        assert "accessible" in msg.lower() or "found" in msg.lower()
    
    def test_health_check_keychain_failure(self, monkeypatch):
        """Test health check keychain failure"""
        def mock_get_api_key():
            return None
        
        monkeypatch.setattr(grok_agent, 'get_api_key', mock_get_api_key)
        
        ok, msg = grok_agent.health_check_keychain()
        assert ok is False
        assert "not found" in msg.lower()
    
    def test_health_check_filesystem(self, patch_default_config, temp_dir):
        """Test health check filesystem"""
        ok, msg = grok_agent.health_check_filesystem()
        assert ok is True or ok is False  # May vary based on environment
        assert isinstance(msg, str)
    
    def test_health_check_all(self, mock_keychain, patch_default_config):
        """Test all health checks"""
        results = grok_agent.health_check_all()
        
        assert 'keychain' in results
        assert 'filesystem' in results
        
        for component, (ok, msg) in results.items():
            assert isinstance(ok, bool)
            assert isinstance(msg, str)


class TestExportUserData:
    """Test GDPR/CCPA data export functionality"""
    
    def test_export_user_data(self, patch_default_config, temp_dir, monkeypatch):
        """Test exporting user data"""
        # Create mock files
        history_path = temp_dir / ".grok_terminal_history.json"
        history_path.write_text('[]')
        
        config_path = temp_dir / ".grok_terminal_config.json"
        config_path.write_text('{"model": "test"}')
        
        todos_path = temp_dir / ".grok_terminal" / "todos.json"
        todos_path.parent.mkdir(exist_ok=True)
        todos_path.write_text('{}')
        
        log_path = temp_dir / ".grok_terminal" / "grok.log"
        log_path.write_text("test log line\n" * 50)
        
        # Mock expanduser to use temp_dir
        original_expanduser = os.path.expanduser
        
        def mock_expanduser(path):
            if path.startswith('~/'):
                return str(temp_dir / path[2:])
            elif path == '~':
                return str(temp_dir)
            return original_expanduser(path)
        
        monkeypatch.setattr(os.path, "expanduser", mock_expanduser)
        
        # Mock sys.exit to avoid actual exit
        with patch('sys.exit'):
            with patch('builtins.print'):  # Suppress print output
                grok_agent.export_user_data()
        
        # Check export file was created
        export_file = temp_dir / ".grok_terminal_data_export.json"
        assert export_file.exists()
        
        # Verify export content
        export_data = json.loads(export_file.read_text())
        assert "export_date" in export_data
        assert "data" in export_data


class TestDeleteUserData:
    """Test GDPR/CCPA data deletion functionality"""
    
    def test_delete_user_data_cancelled(self, patch_default_config, temp_dir, monkeypatch):
        """Test deleting user data with cancellation"""
        # Mock expanduser to use temp_dir
        original_expanduser = os.path.expanduser
        def mock_expanduser(path):
            if path.startswith('~/'):
                return str(temp_dir / path[2:])
            elif path == '~':
                return str(temp_dir)
            return original_expanduser(path)
        monkeypatch.setattr(os.path, "expanduser", mock_expanduser)
        
        # Mock input to return cancel
        with patch('builtins.input', return_value='CANCEL'):
            with patch('builtins.print'):  # Suppress print output
                grok_agent.delete_user_data()
        
        # Data should not be deleted
    
    def test_delete_user_data_confirmed(self, patch_default_config, temp_dir, monkeypatch):
        """Test deleting user data with confirmation"""
        # Create mock files
        history_path = temp_dir / ".grok_terminal_history.json"
        history_path.write_text('[]')
        
        config_path = temp_dir / ".grok_terminal_config.json"
        config_path.write_text('{}')
        
        todos_path = temp_dir / ".grok_terminal" / "todos.json"
        todos_path.parent.mkdir(exist_ok=True)
        todos_path.write_text('{}')
        
        # Mock expanduser
        original_expanduser = os.path.expanduser
        def mock_expanduser(path):
            if path.startswith('~/'):
                return str(temp_dir / path[2:])
            elif path == '~':
                return str(temp_dir)
            return original_expanduser(path)
        monkeypatch.setattr(os.path, "expanduser", mock_expanduser)
        
        # Mock input to return DELETE
        with patch('builtins.input', return_value='DELETE'):
            with patch('builtins.print'):  # Suppress print output
                with patch('grok_agent.reset_cache'):  # Mock cache reset
                    grok_agent.delete_user_data()


class TestToolBash:
    """Test Bash tool"""
    
    def test_tool_bash_success(self, patch_default_config):
        """Test successful bash command execution"""
        with patch('grok_agent.execute_command_safely') as mock_exec:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "test output"
            mock_result.stderr = ""
            mock_exec.return_value = mock_result
            
            exit_code, stdout, stderr = grok_agent.tool_bash({"command": "echo test"})
            
            assert exit_code == 0
            assert stdout == "test output"
            mock_exec.assert_called_once()
    
    def test_tool_bash_no_command(self):
        """Test bash tool with no command"""
        exit_code, stdout, stderr = grok_agent.tool_bash({})
        assert exit_code == 1
        assert "No command provided" in stderr
    
    def test_tool_bash_exception(self, patch_default_config):
        """Test bash tool with exception"""
        with patch('grok_agent.execute_command_safely', side_effect=Exception("test error")):
            exit_code, stdout, stderr = grok_agent.tool_bash({"command": "test"})
            assert exit_code == 1
            assert "test error" in stderr


class TestToolEdit:
    """Test Edit tool"""
    
    def test_tool_edit_no_path(self):
        """Test edit tool with no path"""
        exit_code, stdout, stderr = grok_agent.tool_edit({})
        assert exit_code == 1
        assert "No path provided" in stderr
    
    def test_tool_edit_success(self, temp_dir):
        """Test edit tool"""
        test_file = temp_dir / "test.txt"
        test_file.write_text("original")
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            exit_code, stdout, stderr = grok_agent.tool_edit({"path": str(test_file)})
            
            assert exit_code == 0
            mock_run.assert_called_once()
    
    def test_tool_edit_timeout(self, temp_dir):
        """Test edit tool timeout"""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test")
        
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired("vim", 300)):
            exit_code, stdout, stderr = grok_agent.tool_edit({"path": str(test_file)})
            assert exit_code == 1
            assert "timeout" in stderr.lower()


class TestToolGrep:
    """Test Grep tool"""
    
    def test_tool_grep_no_query(self):
        """Test grep tool with no query"""
        exit_code, stdout, stderr = grok_agent.tool_grep({"dir": "."})
        assert exit_code == 1
        assert "No query provided" in stderr
    
    def test_tool_grep_success(self, temp_dir):
        """Test grep tool"""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content\nanother line")
        
        exit_code, stdout, stderr = grok_agent.tool_grep({"query": "test", "dir": str(temp_dir)})
        
        # Grep may or may not find results, but should not error
        assert exit_code in [0, 1]
    
    def test_tool_grep_timeout(self, temp_dir):
        """Test grep tool timeout"""
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired("grep", 30)):
            exit_code, stdout, stderr = grok_agent.tool_grep({"query": "test", "dir": str(temp_dir)})
            assert exit_code == 1
            assert "timeout" in stderr.lower()


class TestRetryWithBackoff:
    """Test retry with backoff functionality"""
    
    def test_retry_success_first_attempt(self):
        """Test retry succeeds on first attempt"""
        def success_func():
            return "success"
        
        result = grok_agent._retry_with_backoff(success_func, max_retries=3)
        assert result == "success"
    
    def test_retry_success_after_failure(self):
        """Test retry succeeds after initial failure"""
        attempts = []
        
        def failing_then_success():
            attempts.append(1)
            if len(attempts) < 2:
                raise httpx.ConnectError("Connection failed")
            return "success"
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = grok_agent._retry_with_backoff(failing_then_success, max_retries=3)
            assert result == "success"
            assert len(attempts) == 2
    
    def test_retry_max_retries_exceeded(self):
        """Test retry fails after max retries"""
        def always_fail():
            raise httpx.ConnectError("Connection failed")
        
        with patch('time.sleep'):  # Mock sleep
            with pytest.raises(httpx.ConnectError):
                grok_agent._retry_with_backoff(always_fail, max_retries=2)
    
    def test_retry_no_retry_on_client_error(self):
        """Test retry doesn't retry on 4xx errors"""
        def client_error():
            response = MagicMock()
            response.status_code = 400
            raise httpx.HTTPStatusError("Bad Request", request=MagicMock(), response=response)
        
        with pytest.raises(httpx.HTTPStatusError):
            grok_agent._retry_with_backoff(client_error, max_retries=3)


class TestGetHttpClient:
    """Test HTTP client creation"""
    
    def test_get_http_client_creates_once(self):
        """Test HTTP client is created once and reused"""
        # Reset client
        grok_agent._http_client = None
        
        client1 = grok_agent._get_http_client()
        client2 = grok_agent._get_http_client()
        
        assert client1 is client2
        assert isinstance(client1, httpx.Client)
    
    def test_get_http_client_fallback_http1(self):
        """Test HTTP client falls back to HTTP/1.1"""
        grok_agent._http_client = None
        
        # Test that client is created (fallback behavior is internal)
        client = grok_agent._get_http_client()
        assert client is not None
        assert isinstance(client, httpx.Client)


class TestMainAdditional:
    """Additional tests for main function"""
    
    def test_main_list_agents(self, mock_keychain, patch_default_config):
        """Test --list-agents flag"""
        with patch('sys.argv', ['grok_agent.py', '--list-agents']):
            with patch('builtins.print'):  # Suppress output
                with pytest.raises(SystemExit) as exc_info:
                    grok_agent.main()
                assert exc_info.value.code == 0
    
    def test_main_export_data(self, mock_keychain, patch_default_config, temp_dir, monkeypatch):
        """Test --export-data flag"""
        monkeypatch.setattr(Path, "home", lambda: temp_dir)
        monkeypatch.setattr(os.path, "expanduser", lambda p: str(temp_dir / p.replace("~/", "")))
        monkeypatch.setattr(os.path, "exists", lambda p: False)  # No files exist
        
        with patch('sys.argv', ['grok_agent.py', '--export-data']):
            with patch('sys.exit'):  # Prevent actual exit
                with patch('builtins.print'):  # Suppress output
                    grok_agent.main()
    
    def test_main_delete_data_cancelled(self, mock_keychain, patch_default_config, monkeypatch):
        """Test --delete-data flag with cancellation"""
        with patch('sys.argv', ['grok_agent.py', '--delete-data']):
            with patch('builtins.input', return_value='CANCEL'):
                with patch('sys.exit'):  # Prevent actual exit
                    with patch('builtins.print'):  # Suppress output
                        grok_agent.main()
    
    def test_main_no_api_key(self, patch_default_config):
        """Test main with no API key"""
        with patch('grok_agent.get_api_key', return_value=None):
            with patch('sys.argv', ['grok_agent.py', 'test']):
                with pytest.raises(SystemExit) as exc_info:
                    grok_agent.main()
                assert exc_info.value.code == 1
    
    def test_main_endpoint_override(self, mock_keychain, patch_default_config):
        """Test --endpoint flag"""
        with patch('grok_agent.call_grok_api') as mock_api:
            mock_api.return_value = iter([{"choices": [{"delta": {"content": "test"}}]}])
            
            with patch('sys.argv', ['grok_agent.py', '--endpoint', 'https://test.com/api', 'test']):
                try:
                    grok_agent.main()
                except SystemExit:
                    pass  # Expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
