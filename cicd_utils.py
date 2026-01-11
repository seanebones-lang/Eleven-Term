#!/usr/bin/env python3
"""
CI/CD Utilities for NextEleven Terminal Agent
Provides CI/CD pipeline management capabilities
"""

import subprocess
import json
from typing import Dict, Any, Tuple, Optional


def gh_workflow_list(repo: Optional[str] = None) -> Tuple[int, str, str]:
    """List GitHub Actions workflows"""
    try:
        cmd = ['gh', 'workflow', 'list']
        if repo:
            cmd.extend(['--repo', repo])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "gh (GitHub CLI) not found. Install with: brew install gh"
    except subprocess.TimeoutExpired:
        return 1, "", "gh timeout"
    except Exception as e:
        return 1, "", str(e)


def gh_workflow_run(workflow: str, repo: Optional[str] = None, ref: str = "main") -> Tuple[int, str, str]:
    """Run GitHub Actions workflow"""
    try:
        cmd = ['gh', 'workflow', 'run', workflow, '--ref', ref]
        if repo:
            cmd.extend(['--repo', repo])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "gh (GitHub CLI) not found"
    except subprocess.TimeoutExpired:
        return 1, "", "gh timeout"
    except Exception as e:
        return 1, "", str(e)


def gh_run_list(repo: Optional[str] = None, limit: int = 10) -> Tuple[int, str, str]:
    """List GitHub Actions workflow runs"""
    try:
        cmd = ['gh', 'run', 'list', '--limit', str(limit)]
        if repo:
            cmd.extend(['--repo', repo])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "gh (GitHub CLI) not found"
    except subprocess.TimeoutExpired:
        return 1, "", "gh timeout"
    except Exception as e:
        return 1, "", str(e)


def gh_run_view(run_id: str, repo: Optional[str] = None) -> Tuple[int, str, str]:
    """View GitHub Actions workflow run details"""
    try:
        cmd = ['gh', 'run', 'view', run_id]
        if repo:
            cmd.extend(['--repo', repo])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "gh (GitHub CLI) not found"
    except subprocess.TimeoutExpired:
        return 1, "", "gh timeout"
    except Exception as e:
        return 1, "", str(e)


def gh_run_watch(run_id: str, repo: Optional[str] = None) -> Tuple[int, str, str]:
    """Watch GitHub Actions workflow run"""
    try:
        cmd = ['gh', 'run', 'watch', run_id]
        if repo:
            cmd.extend(['--repo', repo])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "gh (GitHub CLI) not found"
    except subprocess.TimeoutExpired:
        return 1, "", "gh timeout"
    except Exception as e:
        return 1, "", str(e)
