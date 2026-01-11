#!/usr/bin/env python3
"""
Load Testing Utilities for NextEleven Terminal Agent
Provides load and stress testing capabilities
"""

import subprocess
import json
import os
import tempfile
from typing import Dict, Any, Tuple, Optional


def k6_run(script_path: str, duration: str = "30s", vus: int = 10, output_format: str = "json") -> Tuple[int, str, str]:
    """Run k6 load test"""
    try:
        cmd = ['k6', 'run', '--duration', duration, '--vus', str(vus), '--out', f'json={output_format}', script_path]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "k6 not found. Install with: brew install k6"
    except subprocess.TimeoutExpired:
        return 1, "", "k6 test timeout"
    except Exception as e:
        return 1, "", str(e)


def k6_simple_url(url: str, duration: str = "30s", vus: int = 10) -> Tuple[int, str, str]:
    """Run simple k6 load test against URL"""
    try:
        # Create temporary k6 script
        script = f"""
import http from 'k6/http';
import {{ check }} from 'k6';

export default function () {{
  const res = http.get('{url}');
  check(res, {{ 'status was 200': (r) => r.status == 200 }});
}}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(script)
            script_path = f.name
        
        result = k6_run(script_path, duration, vus)
        os.unlink(script_path)
        return result
    except Exception as e:
        return 1, "", str(e)


def wrk_benchmark(url: str, threads: int = 4, connections: int = 10, duration: str = "30s") -> Tuple[int, str, str]:
    """Run wrk HTTP benchmark"""
    try:
        cmd = ['wrk', '-t', str(threads), '-c', str(connections), '-d', duration, url]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "wrk not found. Install with: brew install wrk"
    except subprocess.TimeoutExpired:
        return 1, "", "wrk timeout"
    except Exception as e:
        return 1, "", str(e)


def ab_benchmark(url: str, requests: int = 1000, concurrency: int = 10) -> Tuple[int, str, str]:
    """Run Apache Bench (ab) benchmark"""
    try:
        cmd = ['ab', '-n', str(requests), '-c', str(concurrency), url]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "ab (Apache Bench) not found"
    except subprocess.TimeoutExpired:
        return 1, "", "ab timeout"
    except Exception as e:
        return 1, "", str(e)


def locust_run(script_path: str, host: str, users: int = 10, spawn_rate: int = 2, run_time: str = "1m", headless: bool = True) -> Tuple[int, str, str]:
    """Run locust load test"""
    try:
        cmd = ['locust', '-f', script_path, '--host', host, '--users', str(users), '--spawn-rate', str(spawn_rate), '--run-time', run_time]
        if headless:
            cmd.append('--headless')
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "locust not found. Install with: brew install locust"
    except subprocess.TimeoutExpired:
        return 1, "", "locust timeout"
    except Exception as e:
        return 1, "", str(e)
