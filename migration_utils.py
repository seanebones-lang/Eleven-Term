#!/usr/bin/env python3
"""
Database Migration Utilities for NextEleven Terminal Agent
Provides database schema migration capabilities
"""

import subprocess
import os
from typing import Dict, Any, Tuple, Optional
from pathlib import Path


def alembic_current(directory: str = ".") -> Tuple[int, str, str]:
    """Show current Alembic migration revision"""
    try:
        cmd = ['alembic', 'current']
        result = subprocess.run(cmd, cwd=directory, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "alembic not found. Install with: pip install alembic"
    except subprocess.TimeoutExpired:
        return 1, "", "alembic timeout"
    except Exception as e:
        return 1, "", str(e)


def alembic_history(directory: str = ".", verbose: bool = False) -> Tuple[int, str, str]:
    """Show Alembic migration history"""
    try:
        cmd = ['alembic', 'history']
        if verbose:
            cmd.append('--verbose')
        result = subprocess.run(cmd, cwd=directory, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "alembic not found"
    except subprocess.TimeoutExpired:
        return 1, "", "alembic timeout"
    except Exception as e:
        return 1, "", str(e)


def alembic_upgrade(revision: str = "head", directory: str = ".") -> Tuple[int, str, str]:
    """Upgrade database to revision using Alembic"""
    try:
        cmd = ['alembic', 'upgrade', revision]
        result = subprocess.run(cmd, cwd=directory, capture_output=True, text=True, timeout=300)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "alembic not found"
    except subprocess.TimeoutExpired:
        return 1, "", "alembic timeout"
    except Exception as e:
        return 1, "", str(e)


def alembic_downgrade(revision: str, directory: str = ".") -> Tuple[int, str, str]:
    """Downgrade database to revision using Alembic"""
    try:
        cmd = ['alembic', 'downgrade', revision]
        result = subprocess.run(cmd, cwd=directory, capture_output=True, text=True, timeout=300)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "alembic not found"
    except subprocess.TimeoutExpired:
        return 1, "", "alembic timeout"
    except Exception as e:
        return 1, "", str(e)


def dbmate_up(database_url: Optional[str] = None) -> Tuple[int, str, str]:
    """Run dbmate migrations up"""
    try:
        env = os.environ.copy()
        if database_url:
            env['DATABASE_URL'] = database_url
        
        cmd = ['dbmate', 'up']
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=300)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "dbmate not found. Install with: brew install dbmate"
    except subprocess.TimeoutExpired:
        return 1, "", "dbmate timeout"
    except Exception as e:
        return 1, "", str(e)


def dbmate_down(database_url: Optional[str] = None) -> Tuple[int, str, str]:
    """Rollback dbmate migrations"""
    try:
        env = os.environ.copy()
        if database_url:
            env['DATABASE_URL'] = database_url
        
        cmd = ['dbmate', 'down']
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=300)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "dbmate not found"
    except subprocess.TimeoutExpired:
        return 1, "", "dbmate timeout"
    except Exception as e:
        return 1, "", str(e)


def dbmate_status(database_url: Optional[str] = None) -> Tuple[int, str, str]:
    """Show dbmate migration status"""
    try:
        env = os.environ.copy()
        if database_url:
            env['DATABASE_URL'] = database_url
        
        cmd = ['dbmate', 'status']
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "dbmate not found"
    except subprocess.TimeoutExpired:
        return 1, "", "dbmate timeout"
    except Exception as e:
        return 1, "", str(e)
