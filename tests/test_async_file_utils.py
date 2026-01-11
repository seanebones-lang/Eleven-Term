"""Tests for async_file_utils"""
import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from async_file_utils import (
    async_load_config, async_save_history, async_load_history,
    async_load_todos, async_save_todos, async_read_file, async_write_file
)

@pytest.mark.asyncio
class TestAsyncFileUtils:
    """Test async file utilities"""
    
    def test_async_load_config_nonexistent(self):
        """Test loading non-existent config"""
        async def run():
            config = await async_load_config("/nonexistent/config.json")
            assert config == {}
        
        asyncio.run(run())
    
    def test_async_save_and_load_history(self):
        """Test saving and loading history"""
        async def run():
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
                temp_path = f.name
            
            try:
                history = [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there"}
                ]
                
                await async_save_history(history, temp_path, max_messages=10)
                
                loaded = await async_load_history(temp_path)
                assert len(loaded) == 2
                assert loaded[0]["role"] == "user"
            finally:
                Path(temp_path).unlink()
        
        asyncio.run(run())
    
    def test_async_save_and_load_todos(self):
        """Test saving and loading todos"""
        async def run():
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
                temp_path = f.name
            
            try:
                todos = {"todo1": "Task 1", "todo2": "Task 2"}
                
                await async_save_todos(todos, temp_path)
                
                loaded = await async_load_todos(temp_path)
                assert loaded == todos
            finally:
                Path(temp_path).unlink()
        
        asyncio.run(run())
    
    def test_async_read_write_file(self):
        """Test async file read/write"""
        async def run():
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                temp_path = f.name
            
            try:
                content = "Test content"
                success = await async_write_file(temp_path, content)
                assert success
                
                read_content = await async_read_file(temp_path)
                assert read_content == content
            finally:
                Path(temp_path).unlink()
        
        asyncio.run(run())