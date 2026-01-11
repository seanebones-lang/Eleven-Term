"""
Benchmark startup time and file I/O performance
"""
import pytest
import time
import subprocess
import sys
from pathlib import Path

@pytest.mark.benchmark
class TestStartupTime:
    """Benchmark startup and initialization performance"""
    
    def test_import_time(self, benchmark):
        """Measure time to import grok_agent module"""
        def import_module():
            import importlib
            if 'grok_agent' in sys.modules:
                importlib.reload(sys.modules['grok_agent'])
            else:
                import grok_agent
        
        benchmark(import_module)
    
    def test_config_load_time(self, benchmark):
        """Measure time to load configuration"""
        from grok_agent import load_config
        
        def load_cfg():
            return load_config()
        
        result = benchmark(load_cfg)
        assert result is not None
        # Target: <50ms
        assert benchmark.stats.mean < 0.05, f"Config load time {benchmark.stats.mean*1000:.2f}ms exceeds 50ms"
    
    def test_history_load_time(self, benchmark):
        """Measure time to load history"""
        from grok_agent import load_history
        
        def load_hist():
            return load_history()
        
        result = benchmark(load_hist)
        assert result is not None
        # Target: <100ms for typical history file
        assert benchmark.stats.mean < 0.1, f"History load time {benchmark.stats.mean*1000:.2f}ms exceeds 100ms"