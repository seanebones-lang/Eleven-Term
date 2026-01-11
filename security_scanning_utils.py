#!/usr/bin/env python3
"""
Security Scanning Utilities for NextEleven Terminal Agent
Provides security vulnerability scanning capabilities
"""

import subprocess
import json
import os
from typing import Dict, Any, Tuple, Optional
from pathlib import Path


def snyk_test(path: str = ".", severity_threshold: str = "low") -> Tuple[int, str, str]:
    """Run Snyk security test"""
    try:
        cmd = ['snyk', 'test', '--severity-threshold', severity_threshold, '--json', path]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        # Try to parse JSON output
        try:
            data = json.loads(result.stdout)
            summary = f"Found {len(data.get('vulnerabilities', []))} vulnerabilities"
            return result.returncode, summary + "\n" + result.stdout, result.stderr
        except (json.JSONDecodeError, ValueError):
            return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "snyk not found. Install with: brew install snyk or npm install -g snyk"
    except subprocess.TimeoutExpired:
        return 1, "", "snyk timeout"
    except Exception as e:
        return 1, "", str(e)


def trivy_scan_image(image: str, severity: str = "UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL") -> Tuple[int, str, str]:
    """Scan container image with Trivy"""
    try:
        cmd = ['trivy', 'image', '--severity', severity, '--format', 'json', image]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        try:
            data = json.loads(result.stdout)
            vuln_count = len(data.get('Results', [{}])[0].get('Vulnerabilities', []))
            summary = f"Found {vuln_count} vulnerabilities"
            return result.returncode, summary + "\n" + result.stdout, result.stderr
        except (json.JSONDecodeError, ValueError, IndexError, KeyError):
            return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "trivy not found. Install with: brew install trivy"
    except subprocess.TimeoutExpired:
        return 1, "", "trivy timeout"
    except Exception as e:
        return 1, "", str(e)


def trivy_scan_filesystem(path: str = ".", severity: str = "UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL") -> Tuple[int, str, str]:
    """Scan filesystem with Trivy"""
    try:
        cmd = ['trivy', 'filesystem', '--severity', severity, '--format', 'json', path]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        try:
            data = json.loads(result.stdout)
            vuln_count = len(data.get('Results', [{}])[0].get('Vulnerabilities', []))
            summary = f"Found {vuln_count} vulnerabilities"
            return result.returncode, summary + "\n" + result.stdout, result.stderr
        except (json.JSONDecodeError, ValueError, IndexError, KeyError):
            return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "trivy not found. Install with: brew install trivy"
    except subprocess.TimeoutExpired:
        return 1, "", "trivy timeout"
    except Exception as e:
        return 1, "", str(e)


def semgrep_scan(path: str = ".", config: str = "auto") -> Tuple[int, str, str]:
    """Run Semgrep security scan"""
    try:
        cmd = ['semgrep', '--config', config, '--json', path]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        try:
            data = json.loads(result.stdout)
            findings_count = len(data.get('results', []))
            summary = f"Found {findings_count} security findings"
            return result.returncode, summary + "\n" + result.stdout, result.stderr
        except (json.JSONDecodeError, ValueError, KeyError):
            return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "semgrep not found. Install with: brew install semgrep"
    except subprocess.TimeoutExpired:
        return 1, "", "semgrep timeout"
    except Exception as e:
        return 1, "", str(e)


def bandit_scan(path: str = ".", severity_level: int = 1) -> Tuple[int, str, str]:
    """Run Bandit security scan (Python)"""
    try:
        cmd = ['bandit', '-r', '-f', 'json', '-ll', str(severity_level), path]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        try:
            data = json.loads(result.stdout)
            metrics = data.get('metrics', {})
            total = metrics.get('_totals', {}).get('SEVERITY', {}).get('HIGH', 0) + \
                   metrics.get('_totals', {}).get('SEVERITY', {}).get('MEDIUM', 0) + \
                   metrics.get('_totals', {}).get('SEVERITY', {}).get('LOW', 0)
            summary = f"Found {total} security issues"
            return result.returncode, summary + "\n" + result.stdout, result.stderr
        except (json.JSONDecodeError, ValueError, KeyError):
            return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "bandit not found. Install with: pip install bandit"
    except subprocess.TimeoutExpired:
        return 1, "", "bandit timeout"
    except Exception as e:
        return 1, "", str(e)
