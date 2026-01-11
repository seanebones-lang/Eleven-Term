#!/usr/bin/env python3
"""
Profiling Utilities for NextEleven Terminal Agent
Provides performance profiling capabilities
"""

import subprocess
import sys
import os
import cProfile
import pstats
import io
from typing import Dict, Any, Tuple, Optional
from pathlib import Path


def profile_python_script(script_path: str, args: Optional[list] = None, output_file: Optional[str] = None) -> Tuple[int, str, str]:
    """Profile a Python script using cProfile"""
    try:
        cmd = [sys.executable, '-m', 'cProfile', '-o', output_file or '/tmp/profile.stats', script_path]
        if args:
            cmd.extend(args)
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Profiling timeout"
    except Exception as e:
        return 1, "", str(e)


def analyze_profile_stats(stats_file: str, top_n: int = 20) -> Tuple[int, str, str]:
    """Analyze cProfile stats file and return top N functions"""
    try:
        import pstats
        stats = pstats.Stats(stats_file)
        
        # Capture output
        output = io.StringIO()
        stats.sort_stats('cumulative')
        stats.print_stats(top_n, stream=output)
        
        return 0, output.getvalue(), ""
    except Exception as e:
        return 1, "", str(e)


def py_spy_record(pid: Optional[int] = None, duration: int = 10, output_file: Optional[str] = None) -> Tuple[int, str, str]:
    """Record Python process using py-spy"""
    try:
        if not pid:
            return 1, "", "Process ID required"
        
        output_file = output_file or f'/tmp/py-spy-{pid}.svg'
        cmd = ['py-spy', 'record', '-o', output_file, '--pid', str(pid), '--duration', str(duration)]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=duration + 10)
        return result.returncode, f"Profile saved to {output_file}", result.stderr
    except FileNotFoundError:
        return 1, "", "py-spy not found. Install with: brew install py-spy"
    except subprocess.TimeoutExpired:
        return 1, "", "py-spy timeout"
    except Exception as e:
        return 1, "", str(e)


def py_spy_top(pid: Optional[int] = None, duration: int = 10) -> Tuple[int, str, str]:
    """Show top Python functions using py-spy"""
    try:
        if not pid:
            return 1, "", "Process ID required"
        
        cmd = ['py-spy', 'top', '--pid', str(pid), '--duration', str(duration)]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=duration + 10)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "py-spy not found. Install with: brew install py-spy"
    except subprocess.TimeoutExpired:
        return 1, "", "py-spy timeout"
    except Exception as e:
        return 1, "", str(e)


def memory_profile_script(script_path: str, args: Optional[list] = None) -> Tuple[int, str, str]:
    """Profile memory usage of a Python script"""
    try:
        cmd = [sys.executable, '-m', 'memory_profiler', script_path]
        if args:
            cmd.extend(args)
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "memory_profiler not found. Install with: pip install memory-profiler"
    except subprocess.TimeoutExpired:
        return 1, "", "Memory profiling timeout"
    except Exception as e:
        return 1, "", str(e)
