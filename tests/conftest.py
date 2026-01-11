"""
Pytest fixtures for Grok Terminal Agent tests
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest


@pytest.fixture
def temp_dir(tmp_path):
    """Create temporary directory for test files"""
    return tmp_path


@pytest.fixture
def mock_history_file(temp_dir):
    """Create mock history file"""
    history_file = temp_dir / ".grok_terminal_history.json"
    history_data = [
        {"role": "user", "content": "test query"},
        {"role": "assistant", "content": "test response"}
    ]
    history_file.write_text(json.dumps(history_data))
    os.chmod(history_file, 0o600)
    return str(history_file)


@pytest.fixture
def mock_config_file(temp_dir):
    """Create mock config file"""
    config_file = temp_dir / ".grok_terminal_config.json"
    config_data = {
        "model": "grok-4.1-fast",
        "temperature": 0.1,
        "max_tokens": 2048
    }
    config_file.write_text(json.dumps(config_data))
    os.chmod(config_file, 0o600)
    return str(config_file)


@pytest.fixture
def mock_todos_file(temp_dir):
    """Create mock todos file"""
    todos_file = temp_dir / "todos.json"
    todos_data = {
        "2026-01-01T00:00:00": "test todo"
    }
    todos_file.write_text(json.dumps(todos_data))
    os.chmod(todos_file, 0o600)
    return str(todos_file)


@pytest.fixture
def mock_api_key():
    """Mock API key"""
    return "xai-test-api-key-12345"


@pytest.fixture
def mock_keychain(monkeypatch, mock_api_key):
    """Mock macOS Keychain access"""
    def mock_find_generic_password(*args, **kwargs):
        result = MagicMock()
        result.stdout = mock_api_key
        result.returncode = 0
        return result
    
    monkeypatch.setattr(
        "subprocess.run",
        lambda *args, **kwargs: mock_find_generic_password()
    )
    return mock_api_key


@pytest.fixture
def mock_grok_api_response():
    """Mock Grok API response"""
    return {
        "choices": [{
            "message": {
                "content": "Test response from Grok"
            }
        }]
    }


@pytest.fixture
def mock_grok_api_stream():
    """Mock Grok API streaming response"""
    def stream_generator():
        yield {"choices": [{"delta": {"content": "Test "}}]}
        yield {"choices": [{"delta": {"content": "streaming "}}]}
        yield {"choices": [{"delta": {"content": "response"}}]}
    return stream_generator()


@pytest.fixture
def mock_env_context():
    """Mock environment context"""
    return (
        "/test/cwd",
        "M  modified_file.txt\nA  new_file.txt",
        "test/\n  file1.py\n  file2.py"
    )


@pytest.fixture
def mock_subprocess(monkeypatch):
    """Mock subprocess calls"""
    mock_results = {}
    
    def mock_run(*args, **kwargs):
        cmd = args[0] if args else []
        cmd_str = ' '.join(cmd) if isinstance(cmd, list) else str(cmd)
        
        # Default mock result
        result = MagicMock()
        result.returncode = 0
        result.stdout = "mock output"
        result.stderr = ""
        
        # Customize based on command
        if 'git' in cmd_str and 'status' in cmd_str:
            result.stdout = "M  test.txt\n"
        elif 'tree' in cmd_str:
            result.returncode = 1  # tree not available, should fallback
        elif 'ls' in cmd_str:
            result.stdout = "file1.py\nfile2.txt\n"
        
        return result
    
    monkeypatch.setattr("subprocess.run", mock_run)
    return mock_run


@pytest.fixture(autouse=True)
def reset_http_client():
    """Reset HTTP client cache before each test"""
    import grok_agent
    from collections import OrderedDict
    grok_agent._http_client = None
    grok_agent._response_cache = OrderedDict()
    if hasattr(grok_agent, '_cache_stats'):
        grok_agent._cache_stats = {"hits": 0, "misses": 0, "evictions": 0}
    yield
    # Clean up after test
    grok_agent._http_client = None
    grok_agent._response_cache = OrderedDict()
    if hasattr(grok_agent, '_cache_stats'):
        grok_agent._cache_stats = {"hits": 0, "misses": 0, "evictions": 0}


@pytest.fixture
def patch_default_config(temp_dir, monkeypatch):
    """Patch default config paths to use temp directory"""
    import grok_agent
    
    original_history = grok_agent.DEFAULT_CONFIG['history_file']
    original_todos = grok_agent.DEFAULT_CONFIG['todos_file']
    original_hooks = grok_agent.DEFAULT_CONFIG['hooks_dir']
    
    grok_agent.DEFAULT_CONFIG['history_file'] = str(temp_dir / ".grok_terminal_history.json")
    grok_agent.DEFAULT_CONFIG['todos_file'] = str(temp_dir / "todos.json")
    grok_agent.DEFAULT_CONFIG['hooks_dir'] = str(temp_dir / "hooks")
    
    # Patch config path for load_config to use temp directory
    config_file = temp_dir / ".grok_terminal_config.json"
    original_load_config = grok_agent.load_config
    
    def patched_load_config(config_path=None):
        if config_path is None:
            config_path = str(config_file)
        return original_load_config(config_path)
    
    monkeypatch.setattr(grok_agent, 'load_config', patched_load_config)
    
    yield
    
    # Restore original config
    grok_agent.DEFAULT_CONFIG['history_file'] = original_history
    grok_agent.DEFAULT_CONFIG['todos_file'] = original_todos
    grok_agent.DEFAULT_CONFIG['hooks_dir'] = original_hooks
