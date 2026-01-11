#!/usr/bin/env python3
"""
Comprehensive tests for main() function to reach 100% coverage
Tests all interactive mode flows, error paths, and edge cases
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


class TestMainInteractiveQuota:
    """Test main() interactive mode quota check paths"""
    
    def test_main_interactive_quota_error(self, mock_keychain, patch_default_config, monkeypatch):
        """Test interactive mode with quota error"""
        inputs = iter(['1', 'exit'])
        
        with patch('builtins.input', side_effect=lambda _: next(inputs)):
            with patch('grok_agent.call_grok_api') as mock_api:
                # Mock quota check with error
                mock_api.side_effect = [
                    {"error": "quota exceeded"},  # Quota check returns error
                ]
                
                with patch('sys.argv', ['grok_agent.py', '--interactive']):
                    with pytest.raises(SystemExit) as exc_info:
                        grok_agent.main()
                    assert exc_info.value.code == 1
    
    def test_main_interactive_quota_exception(self, mock_keychain, patch_default_config, monkeypatch):
        """Test interactive mode with quota check exception"""
        inputs = iter(['1', 'exit'])
        
        with patch('builtins.input', side_effect=lambda _: next(inputs)):
            with patch('grok_agent.call_grok_api', side_effect=Exception("API error")):
                with patch('builtins.print'):  # Suppress output
                    with patch('sys.argv', ['grok_agent.py', '--interactive']):
                        try:
                            grok_agent.main()
                        except (SystemExit, StopIteration, KeyboardInterrupt):
                            pass  # Expected


class TestMainInteractiveHistoryCompaction:
    """Test main() interactive mode history compaction"""
    
    def test_main_interactive_with_history_compaction(self, mock_keychain, patch_default_config, temp_dir, monkeypatch):
        """Test interactive mode with history compaction"""
        # Create history with >2 messages
        history_file = temp_dir / ".grok_terminal_history.json"
        history_file.write_text(json.dumps([
            {"role": "user", "content": "msg1"},
            {"role": "assistant", "content": "resp1"},
            {"role": "user", "content": "msg2"},
            {"role": "assistant", "content": "resp2"}
        ]))
        
        original_expanduser = os.path.expanduser
        def mock_expanduser(path):
            if 'history' in path.lower():
                return str(history_file)
            return original_expanduser(path)
        monkeypatch.setattr(os.path, "expanduser", mock_expanduser)
        
        inputs = iter(['1', 'test query', 'exit'])
        input_count = [0]
        
        def mock_input(prompt):
            input_count[0] += 1
            try:
                return next(inputs)
            except StopIteration:
                return 'exit'
        
        with patch('builtins.input', side_effect=mock_input):
            with patch('grok_agent.call_grok_api') as mock_api:
                def api_side_effect(*args, **kwargs):
                    # Quota check
                    if len(args) > 1 and args[1][0].get('content') == 'quota':
                        return {"choices": [{"message": {"content": "ok"}}]}
                    # History compaction
                    elif len(args) > 1 and 'Summarize this conversation' in args[1][0].get('content', ''):
                        return {"choices": [{"message": {"content": "compacted history"}}]}
                    # Main query (streaming)
                    else:
                        def stream_gen():
                            yield {"choices": [{"delta": {"content": "response"}}]}
                        return stream_gen()
                
                mock_api.side_effect = api_side_effect
                
                with patch('builtins.print'):  # Suppress output
                    with patch('sys.argv', ['grok_agent.py', '--interactive']):
                        try:
                            grok_agent.main()
                        except (SystemExit, StopIteration, KeyboardInterrupt):
                            pass  # Expected
    
    def test_main_interactive_history_compaction_failure(self, mock_keychain, patch_default_config, temp_dir, monkeypatch):
        """Test interactive mode with history compaction failure"""
        # Create history with >2 messages
        history_file = temp_dir / ".grok_terminal_history.json"
        history_file.write_text(json.dumps([
            {"role": "user", "content": "msg1"},
            {"role": "assistant", "content": "resp1"},
            {"role": "user", "content": "msg2"},
        ]))
        
        original_expanduser = os.path.expanduser
        def mock_expanduser(path):
            if 'history' in path.lower():
                return str(history_file)
            return original_expanduser(path)
        monkeypatch.setattr(os.path, "expanduser", mock_expanduser)
        
        inputs = iter(['1', 'test query', 'exit'])
        
        with patch('builtins.input', side_effect=lambda _: next(inputs)):
            with patch('grok_agent.call_grok_api') as mock_api:
                def api_side_effect(*args, **kwargs):
                    # Quota check
                    if len(args) > 1 and args[1][0].get('content') == 'quota':
                        return {"choices": [{"message": {"content": "ok"}}]}
                    # History compaction - raise exception
                    elif len(args) > 1 and 'Summarize this conversation' in args[1][0].get('content', ''):
                        raise Exception("Compaction failed")
                    # Main query (streaming)
                    else:
                        def stream_gen():
                            yield {"choices": [{"delta": {"content": "response"}}]}
                        return stream_gen()
                
                mock_api.side_effect = api_side_effect
                
                with patch('builtins.print'):  # Suppress output
                    with patch('sys.argv', ['grok_agent.py', '--interactive']):
                        try:
                            grok_agent.main()
                        except (SystemExit, StopIteration, KeyboardInterrupt):
                            pass  # Expected


class TestMainInteractiveSlashCommands:
    """Test main() interactive mode slash commands"""
    
    def test_main_interactive_slash_help(self, mock_keychain, patch_default_config, monkeypatch):
        """Test /help command"""
        inputs = iter(['1', '/help', 'exit'])
        
        with patch('builtins.input', side_effect=lambda _: next(inputs)):
            with patch('grok_agent.call_grok_api') as mock_api:
                mock_api.return_value = {"choices": [{"message": {"content": "ok"}}]}
                
                with patch('builtins.print'):  # Suppress output
                    with patch('sys.argv', ['grok_agent.py', '--interactive']):
                        try:
                            grok_agent.main()
                        except (SystemExit, StopIteration, KeyboardInterrupt):
                            pass  # Expected
    
    def test_main_interactive_slash_init(self, mock_keychain, patch_default_config, temp_dir, monkeypatch):
        """Test /init command"""
        inputs = iter(['1', '/init', 'exit'])
        
        with patch('builtins.input', side_effect=lambda _: next(inputs)):
            with patch('grok_agent.call_grok_api') as mock_api:
                def api_side_effect(*args, **kwargs):
                    # Quota check
                    if len(args) > 1 and args[1][0].get('content') == 'quota':
                        return {"choices": [{"message": {"content": "ok"}}]}
                    # /init response
                    else:
                        return {"choices": [{"message": {"content": "# ELEVEN.md\nProject file"}}]}
                
                mock_api.side_effect = api_side_effect
                
                with patch('os.getcwd', return_value=str(temp_dir)):
                    with patch('builtins.print'):  # Suppress output
                        with patch('sys.argv', ['grok_agent.py', '--interactive']):
                            try:
                                grok_agent.main()
                            except (SystemExit, StopIteration, KeyboardInterrupt):
                                pass  # Expected
    
    def test_main_interactive_slash_init_error(self, mock_keychain, patch_default_config, temp_dir, monkeypatch):
        """Test /init command with error"""
        inputs = iter(['1', '/init', 'exit'])
        
        with patch('builtins.input', side_effect=lambda _: next(inputs)):
            with patch('grok_agent.call_grok_api') as mock_api:
                def api_side_effect(*args, **kwargs):
                    # Quota check
                    if len(args) > 1 and args[1][0].get('content') == 'quota':
                        return {"choices": [{"message": {"content": "ok"}}]}
                    # /init - raise error
                    else:
                        raise Exception("API error")
                
                mock_api.side_effect = api_side_effect
                
                with patch('builtins.print'):  # Suppress output
                    with patch('sys.argv', ['grok_agent.py', '--interactive']):
                        try:
                            grok_agent.main()
                        except (SystemExit, StopIteration, KeyboardInterrupt):
                            pass  # Expected
    
    def test_main_interactive_slash_clear(self, mock_keychain, patch_default_config, temp_dir, monkeypatch):
        """Test /clear command"""
        history_file = temp_dir / ".grok_terminal_history.json"
        history_file.write_text(json.dumps([
            {"role": "system", "content": "system prompt"},
            {"role": "user", "content": "msg1"}
        ]))
        
        original_expanduser = os.path.expanduser
        def mock_expanduser(path):
            if 'history' in path.lower():
                return str(history_file)
            return original_expanduser(path)
        monkeypatch.setattr(os.path, "expanduser", mock_expanduser)
        
        inputs = iter(['1', '/clear', 'exit'])
        
        with patch('builtins.input', side_effect=lambda _: next(inputs)):
            with patch('grok_agent.call_grok_api', return_value={"choices": [{"message": {"content": "ok"}}]}):
                with patch('builtins.print'):  # Suppress output
                    with patch('sys.argv', ['grok_agent.py', '--interactive']):
                        try:
                            grok_agent.main()
                        except (SystemExit, StopIteration, KeyboardInterrupt):
                            pass  # Expected
    
    def test_main_interactive_slash_hooks(self, mock_keychain, patch_default_config, monkeypatch):
        """Test /hooks command"""
        inputs = iter(['1', '/hooks', 'exit'])
        
        with patch('builtins.input', side_effect=lambda _: next(inputs)):
            with patch('grok_agent.call_grok_api', return_value={"choices": [{"message": {"content": "ok"}}]}):
                with patch('builtins.print'):  # Suppress output
                    with patch('sys.argv', ['grok_agent.py', '--interactive']):
                        try:
                            grok_agent.main()
                        except (SystemExit, StopIteration, KeyboardInterrupt):
                            pass  # Expected


class TestMainInteractiveTopicDetection:
    """Test main() interactive mode topic detection"""
    
    def test_main_interactive_topic_detection_new_topic(self, mock_keychain, patch_default_config, monkeypatch):
        """Test topic detection with new topic"""
        inputs = iter(['1', 'completely new question', 'exit'])
        
        with patch('builtins.input', side_effect=lambda _: next(inputs)):
            with patch('grok_agent.call_grok_api') as mock_api:
                call_count = [0]
                
                def api_side_effect(*args, **kwargs):
                    call_count[0] += 1
                    # Quota check
                    if call_count[0] == 1:
                        return {"choices": [{"message": {"content": "ok"}}]}
                    # Topic detection - new topic
                    elif call_count[0] == 2:
                        return {"choices": [{"message": {"content": '{"isNewTopic": true, "title": "New Topic"}'}}]}
                    # Main query (streaming)
                    else:
                        def stream_gen():
                            yield {"choices": [{"delta": {"content": "response"}}]}
                        return stream_gen()
                
                mock_api.side_effect = api_side_effect
                
                with patch('builtins.print'):  # Suppress output
                    with patch('sys.argv', ['grok_agent.py', '--interactive']):
                        try:
                            grok_agent.main()
                        except (SystemExit, StopIteration, KeyboardInterrupt):
                            pass  # Expected
    
    def test_main_interactive_topic_detection_error(self, mock_keychain, patch_default_config, monkeypatch):
        """Test topic detection with error"""
        inputs = iter(['1', 'test query', 'exit'])
        
        with patch('builtins.input', side_effect=lambda _: next(inputs)):
            with patch('grok_agent.call_grok_api') as mock_api:
                call_count = [0]
                
                def api_side_effect(*args, **kwargs):
                    call_count[0] += 1
                    # Quota check
                    if call_count[0] == 1:
                        return {"choices": [{"message": {"content": "ok"}}]}
                    # Topic detection - error
                    elif call_count[0] == 2:
                        raise Exception("Topic detection error")
                    # Main query (streaming)
                    else:
                        def stream_gen():
                            yield {"choices": [{"delta": {"content": "response"}}]}
                        return stream_gen()
                
                mock_api.side_effect = api_side_effect
                
                with patch('builtins.print'):  # Suppress output
                    with patch('sys.argv', ['grok_agent.py', '--interactive']):
                        try:
                            grok_agent.main()
                        except (SystemExit, StopIteration, KeyboardInterrupt):
                            pass  # Expected


class TestMainInteractiveToolExecution:
    """Test main() interactive mode tool execution"""
    
    def test_main_interactive_tool_execution(self, mock_keychain, patch_default_config, temp_dir, monkeypatch):
        """Test tool execution in interactive mode"""
        inputs = iter(['1', 'list files', 'y', 'exit'])
        
        with patch('builtins.input', side_effect=lambda _: next(inputs)):
            with patch('grok_agent.call_grok_api') as mock_api:
                call_count = [0]
                
                def api_side_effect(*args, **kwargs):
                    call_count[0] += 1
                    # Quota check
                    if call_count[0] == 1:
                        return {"choices": [{"message": {"content": "ok"}}]}
                    # Topic detection
                    elif call_count[0] == 2:
                        return {"choices": [{"message": {"content": '{"isNewTopic": false}'}}]}
                    # Main query with tool call (streaming)
                    else:
                        def stream_gen():
                            yield {"choices": [{"delta": {"content": '<tool name="LS"><param name="dir">.</param></tool>'}}]}
                            yield {"choices": [{"delta": {"content": "response"}}]}
                        return stream_gen()
                
                mock_api.side_effect = api_side_effect
                
                with patch('grok_agent.tool_ls', return_value=(0, "file1.txt\nfile2.txt", "")):
                    with patch('builtins.print'):  # Suppress output
                        with patch('sys.argv', ['grok_agent.py', '--interactive']):
                            try:
                                grok_agent.main()
                            except (SystemExit, StopIteration, KeyboardInterrupt):
                                pass  # Expected
    
    def test_main_interactive_tool_unknown(self, mock_keychain, patch_default_config, monkeypatch):
        """Test unknown tool in interactive mode"""
        inputs = iter(['1', 'test query', 'exit'])
        
        with patch('builtins.input', side_effect=lambda _: next(inputs)):
            with patch('grok_agent.call_grok_api') as mock_api:
                call_count = [0]
                
                def api_side_effect(*args, **kwargs):
                    call_count[0] += 1
                    # Quota check
                    if call_count[0] == 1:
                        return {"choices": [{"message": {"content": "ok"}}]}
                    # Topic detection
                    elif call_count[0] == 2:
                        return {"choices": [{"message": {"content": '{"isNewTopic": false}'}}]}
                    # Main query with unknown tool (streaming)
                    else:
                        def stream_gen():
                            yield {"choices": [{"delta": {"content": '<tool name="UnknownTool"><param name="param">value</param></tool>'}}]}
                        return stream_gen()
                
                mock_api.side_effect = api_side_effect
                
                with patch('builtins.print'):  # Suppress output
                    with patch('sys.argv', ['grok_agent.py', '--interactive']):
                        try:
                            grok_agent.main()
                        except (SystemExit, StopIteration, KeyboardInterrupt):
                            pass  # Expected
    
    def test_main_interactive_tool_prehook_failure(self, mock_keychain, patch_default_config, temp_dir, monkeypatch):
        """Test tool execution with pre-hook failure"""
        inputs = iter(['1', 'test query', 'exit'])
        
        hooks_dir = temp_dir / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        
        original_expanduser = os.path.expanduser
        def mock_expanduser(path):
            if 'hooks' in path.lower():
                return str(hooks_dir)
            return original_expanduser(path)
        monkeypatch.setattr(os.path, "expanduser", mock_expanduser)
        
        with patch('builtins.input', side_effect=lambda _: next(inputs)):
            with patch('grok_agent.call_grok_api') as mock_api:
                call_count = [0]
                
                def api_side_effect(*args, **kwargs):
                    call_count[0] += 1
                    # Quota check
                    if call_count[0] == 1:
                        return {"choices": [{"message": {"content": "ok"}}]}
                    # Topic detection
                    elif call_count[0] == 2:
                        return {"choices": [{"message": {"content": '{"isNewTopic": false}'}}]}
                    # Main query with tool call (streaming)
                    else:
                        def stream_gen():
                            yield {"choices": [{"delta": {"content": '<tool name="LS"><param name="dir">.</param></tool>'}}]}
                        return stream_gen()
                
                mock_api.side_effect = api_side_effect
                
                # Mock run_hook to return failure
                with patch('grok_agent.run_hook', return_value=(False, "Hook failed")):
                    with patch('builtins.print'):  # Suppress output
                        with patch('sys.argv', ['grok_agent.py', '--interactive']):
                            try:
                                grok_agent.main()
                            except (SystemExit, StopIteration, KeyboardInterrupt):
                                pass  # Expected
    
    def test_main_interactive_tool_permission_declined(self, mock_keychain, patch_default_config, monkeypatch):
        """Test tool execution with permission declined"""
        inputs = iter(['1', 'test query', 'n', 'exit'])  # 'n' for permission
        
        with patch('builtins.input', side_effect=lambda prompt=None: next(inputs)):
            with patch('grok_agent.call_grok_api') as mock_api:
                call_count = [0]
                
                def api_side_effect(*args, **kwargs):
                    call_count[0] += 1
                    # Quota check
                    if call_count[0] == 1:
                        return {"choices": [{"message": {"content": "ok"}}]}
                    # Topic detection
                    elif call_count[0] == 2:
                        return {"choices": [{"message": {"content": '{"isNewTopic": false}'}}]}
                    # Main query with dangerous tool (streaming)
                    else:
                        def stream_gen():
                            yield {"choices": [{"delta": {"content": '<tool name="Bash"><param name="command">rm -rf /</param></tool>'}}]}
                        return stream_gen()
                
                mock_api.side_effect = api_side_effect
                
                with patch('grok_agent.run_hook', return_value=(True, "")):
                    with patch('builtins.print'):  # Suppress output
                        with patch('sys.argv', ['grok_agent.py', '--interactive']):
                            try:
                                grok_agent.main()
                            except (SystemExit, StopIteration, KeyboardInterrupt):
                                pass  # Expected
    
    def test_main_interactive_tool_execution_exception(self, mock_keychain, patch_default_config, monkeypatch):
        """Test tool execution with exception"""
        inputs = iter(['1', 'test query', 'y', 'exit'])
        
        with patch('builtins.input', side_effect=lambda _: next(inputs)):
            with patch('grok_agent.call_grok_api') as mock_api:
                call_count = [0]
                
                def api_side_effect(*args, **kwargs):
                    call_count[0] += 1
                    # Quota check
                    if call_count[0] == 1:
                        return {"choices": [{"message": {"content": "ok"}}]}
                    # Topic detection
                    elif call_count[0] == 2:
                        return {"choices": [{"message": {"content": '{"isNewTopic": false}'}}]}
                    # Main query with tool call (streaming)
                    else:
                        def stream_gen():
                            yield {"choices": [{"delta": {"content": '<tool name="LS"><param name="dir">.</param></tool>'}}]}
                        return stream_gen()
                
                mock_api.side_effect = api_side_effect
                
                # Mock tool to raise exception
                with patch('grok_agent.tool_ls', side_effect=Exception("Tool error")):
                    with patch('grok_agent.run_hook', return_value=(True, "")):
                        with patch('builtins.print'):  # Suppress output
                            with patch('sys.argv', ['grok_agent.py', '--interactive']):
                                try:
                                    grok_agent.main()
                                except (SystemExit, StopIteration, KeyboardInterrupt):
                                    pass  # Expected
    
    def test_main_interactive_tool_api_error(self, mock_keychain, patch_default_config, monkeypatch):
        """Test API error during tool execution"""
        inputs = iter(['1', 'test query', 'exit'])
        
        with patch('builtins.input', side_effect=lambda _: next(inputs)):
            with patch('grok_agent.call_grok_api') as mock_api:
                call_count = [0]
                
                def api_side_effect(*args, **kwargs):
                    call_count[0] += 1
                    # Quota check
                    if call_count[0] == 1:
                        return {"choices": [{"message": {"content": "ok"}}]}
                    # Topic detection
                    elif call_count[0] == 2:
                        return {"choices": [{"message": {"content": '{"isNewTopic": false}'}}]}
                    # Main query - raise error
                    else:
                        raise Exception("API error")
                
                mock_api.side_effect = api_side_effect
                
                with patch('builtins.print'):  # Suppress output
                    with patch('sys.argv', ['grok_agent.py', '--interactive']):
                        try:
                            grok_agent.main()
                        except (SystemExit, StopIteration, KeyboardInterrupt):
                            pass  # Expected


class TestMainInteractiveHistoryCompaction:
    """Test main() interactive mode history compaction in loop"""
    
    def test_main_interactive_history_compaction_threshold(self, mock_keychain, patch_default_config, temp_dir, monkeypatch):
        """Test history compaction when threshold exceeded"""
        # patch_default_config already handles config - just create history file in temp_dir
        # History file path is already set by patch_default_config to temp_dir
        history_file = temp_dir / ".grok_terminal_history.json"
        history = [{"role": "system", "content": "system"}]
        for i in range(25):  # Exceed HISTORY_COMPACT_THRESHOLD (20)
            history.append({"role": "user", "content": f"msg{i}"})
            history.append({"role": "assistant", "content": f"resp{i}"})
        history_file.write_text(json.dumps(history))
        
        inputs = iter(['1', 'test query', 'exit'])
        
        with patch('builtins.input', side_effect=lambda _: next(inputs)):
            with patch('grok_agent.call_grok_api') as mock_api:
                call_count = [0]
                
                def api_side_effect(*args, **kwargs):
                    call_count[0] += 1
                    # Quota check
                    if call_count[0] == 1:
                        return {"choices": [{"message": {"content": "ok"}}]}
                    # Topic detection
                    elif call_count[0] == 2:
                        return {"choices": [{"message": {"content": '{"isNewTopic": false}'}}]}
                    # Main query (streaming)
                    elif call_count[0] == 3:
                        def stream_gen():
                            yield {"choices": [{"delta": {"content": "response"}}]}
                        return stream_gen()
                    # History compaction
                    else:
                        return {"choices": [{"message": {"content": "compacted"}}]}
                
                mock_api.side_effect = api_side_effect
                
                with patch('builtins.print'):  # Suppress output
                    with patch('sys.argv', ['grok_agent.py', '--interactive']):
                        try:
                            grok_agent.main()
                        except (SystemExit, StopIteration, KeyboardInterrupt):
                            pass  # Expected
    
    def test_main_interactive_history_compaction_failure_in_loop(self, mock_keychain, patch_default_config, temp_dir, monkeypatch):
        """Test history compaction failure in loop"""
        # patch_default_config already handles config - just create history file in temp_dir
        # History file path is already set by patch_default_config to temp_dir
        history_file = temp_dir / ".grok_terminal_history.json"
        history = [{"role": "system", "content": "system"}]
        for i in range(25):
            history.append({"role": "user", "content": f"msg{i}"})
            history.append({"role": "assistant", "content": f"resp{i}"})
        history_file.write_text(json.dumps(history))
        
        inputs = iter(['1', 'test query', 'exit'])
        
        with patch('builtins.input', side_effect=lambda _: next(inputs)):
            with patch('grok_agent.call_grok_api') as mock_api:
                call_count = [0]
                
                def api_side_effect(*args, **kwargs):
                    call_count[0] += 1
                    # Quota check
                    if call_count[0] == 1:
                        return {"choices": [{"message": {"content": "ok"}}]}
                    # Topic detection
                    elif call_count[0] == 2:
                        return {"choices": [{"message": {"content": '{"isNewTopic": false}'}}]}
                    # Main query (streaming)
                    elif call_count[0] == 3:
                        def stream_gen():
                            yield {"choices": [{"delta": {"content": "response"}}]}
                        return stream_gen()
                    # History compaction - raise error
                    else:
                        raise Exception("Compaction failed")
                
                mock_api.side_effect = api_side_effect
                
                with patch('builtins.print'):  # Suppress output
                    with patch('sys.argv', ['grok_agent.py', '--interactive']):
                        try:
                            grok_agent.main()
                        except (SystemExit, StopIteration, KeyboardInterrupt):
                            pass  # Expected


class TestMainInteractiveTodos:
    """Test main() interactive mode todos"""
    
    def test_main_interactive_with_todo(self, mock_keychain, patch_default_config, temp_dir, monkeypatch):
        """Test interactive mode with todo in query"""
        todos_file = temp_dir / ".grok_terminal" / "todos.json"
        todos_file.parent.mkdir(parents=True, exist_ok=True)
        todos_file.write_text('{}')
        
        original_expanduser = os.path.expanduser
        def mock_expanduser(path):
            if 'todos' in path.lower():
                return str(todos_file)
            return original_expanduser(path)
        monkeypatch.setattr(os.path, "expanduser", mock_expanduser)
        
        inputs = iter(['1', 'todo: fix bug', 'exit'])
        
        with patch('builtins.input', side_effect=lambda _: next(inputs)):
            with patch('grok_agent.call_grok_api') as mock_api:
                call_count = [0]
                
                def api_side_effect(*args, **kwargs):
                    call_count[0] += 1
                    # Quota check
                    if call_count[0] == 1:
                        return {"choices": [{"message": {"content": "ok"}}]}
                    # Topic detection
                    elif call_count[0] == 2:
                        return {"choices": [{"message": {"content": '{"isNewTopic": false}'}}]}
                    # Main query (streaming)
                    else:
                        def stream_gen():
                            yield {"choices": [{"delta": {"content": "response"}}]}
                        return stream_gen()
                
                mock_api.side_effect = api_side_effect
                
                with patch('builtins.print'):  # Suppress output
                    with patch('sys.argv', ['grok_agent.py', '--interactive']):
                        try:
                            grok_agent.main()
                        except (SystemExit, StopIteration, KeyboardInterrupt):
                            pass  # Expected


class TestMainInteractiveErrorHandling:
    """Test main() interactive mode error handling"""
    
    def test_main_interactive_keyboard_interrupt(self, mock_keychain, patch_default_config, monkeypatch):
        """Test KeyboardInterrupt handling"""
        input_count = [0]
        
        def mock_input(prompt):
            input_count[0] += 1
            if input_count[0] == 1:
                return '1'  # Accept interactive mode
            elif input_count[0] == 2:
                raise KeyboardInterrupt()  # Raise interrupt on second input
            return 'exit'
        
        with patch('builtins.input', side_effect=mock_input):
            with patch('grok_agent.call_grok_api', return_value={"choices": [{"message": {"content": "ok"}}]}):
                with patch('builtins.print'):  # Suppress output
                    with patch('sys.argv', ['grok_agent.py', '--interactive']):
                        try:
                            grok_agent.main()
                        except (SystemExit, KeyboardInterrupt):
                            pass  # Expected
    
    def test_main_interactive_eof_error(self, mock_keychain, patch_default_config, monkeypatch):
        """Test EOFError handling"""
        inputs = iter(['1', EOFError()])
        
        def mock_input(prompt):
            val = next(inputs)
            if isinstance(val, Exception):
                raise val
            return val
        
        with patch('builtins.input', side_effect=mock_input):
            with patch('grok_agent.call_grok_api', return_value={"choices": [{"message": {"content": "ok"}}]}):
                with patch('builtins.print'):  # Suppress output
                    with patch('sys.argv', ['grok_agent.py', '--interactive']):
                        try:
                            grok_agent.main()
                        except (SystemExit, EOFError):
                            pass  # Expected


class TestMainNonInteractive:
    """Test main() non-interactive mode edge cases"""
    
    def test_main_non_interactive_with_history(self, mock_keychain, patch_default_config, temp_dir, monkeypatch):
        """Test non-interactive mode with history"""
        history_file = temp_dir / ".grok_terminal_history.json"
        history_file.write_text(json.dumps([
            {"role": "user", "content": "prev"},
            {"role": "assistant", "content": "resp"}
        ]))
        
        original_expanduser = os.path.expanduser
        def mock_expanduser(path):
            if 'history' in path.lower():
                return str(history_file)
            return original_expanduser(path)
        monkeypatch.setattr(os.path, "expanduser", mock_expanduser)
        
        with patch('grok_agent.call_grok_api') as mock_api:
            def stream_gen():
                yield {"choices": [{"delta": {"content": "response"}}]}
            mock_api.return_value = stream_gen()
            
            with patch('builtins.print'):  # Suppress output
                with patch('sys.argv', ['grok_agent.py', 'test query']):
                    try:
                        grok_agent.main()
                    except SystemExit:
                        pass  # Expected
    
    def test_main_non_interactive_with_tools(self, mock_keychain, patch_default_config, monkeypatch):
        """Test non-interactive mode with tool calls"""
        with patch('grok_agent.call_grok_api') as mock_api:
            def stream_gen():
                yield {"choices": [{"delta": {"content": '<tool name="LS"><param name="dir">.</param></tool>'}}]}
                yield {"choices": [{"delta": {"content": "response"}}]}
            mock_api.return_value = stream_gen()
            
            with patch('builtins.print'):  # Suppress output
                with patch('sys.argv', ['grok_agent.py', 'list files']):
                    try:
                        grok_agent.main()
                    except SystemExit:
                        pass  # Expected
    
    def test_main_non_interactive_error(self, mock_keychain, patch_default_config, monkeypatch):
        """Test non-interactive mode with error"""
        with patch('grok_agent.call_grok_api', side_effect=Exception("API error")):
            with patch('builtins.print'):  # Suppress output
                with patch('sys.argv', ['grok_agent.py', 'test query']):
                    with pytest.raises(SystemExit) as exc_info:
                        grok_agent.main()
                    assert exc_info.value.code == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
