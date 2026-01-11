#!/usr/bin/env python3
"""
Database Utilities for NextEleven Terminal Agent
Provides functions for connecting to and querying databases
"""

import subprocess
import os
import json
from typing import Dict, Any, Tuple, Optional, List
from pathlib import Path


def execute_mysql_query(host: str, user: str, database: str, query: str, password: Optional[str] = None) -> Tuple[int, str, str]:
    """Execute MySQL query"""
    try:
        cmd = ['mysql', '-h', host, '-u', user, database, '-e', query]
        if password:
            # Use MYSQL_PWD environment variable (less secure but works for CLI)
            env = os.environ.copy()
            env['MYSQL_PWD'] = password
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env)
        else:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "MySQL client not found. Install with: brew install mysql-client"
    except subprocess.TimeoutExpired:
        return 1, "", "Query timeout"
    except Exception as e:
        return 1, "", str(e)


def execute_postgresql_query(host: str, user: str, database: str, query: str, password: Optional[str] = None) -> Tuple[int, str, str]:
    """Execute PostgreSQL query"""
    try:
        # Use PGPASSWORD environment variable
        env = os.environ.copy()
        if password:
            env['PGPASSWORD'] = password
        
        cmd = ['psql', '-h', host, '-U', user, '-d', database, '-c', query, '-t', '-A']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "PostgreSQL client not found. Install with: brew install postgresql@15"
    except subprocess.TimeoutExpired:
        return 1, "", "Query timeout"
    except Exception as e:
        return 1, "", str(e)


def execute_mongodb_query(uri: str, database: str, collection: str, query: str) -> Tuple[int, str, str]:
    """Execute MongoDB query"""
    try:
        # mongosh command format
        script = f"""
        use {database};
        db.{collection}.{query};
        """
        
        cmd = ['mongosh', uri, '--eval', script]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "MongoDB shell not found. Install with: brew install mongosh"
    except subprocess.TimeoutExpired:
        return 1, "", "Query timeout"
    except Exception as e:
        return 1, "", str(e)


def execute_redis_command(host: str, port: int, command: str, password: Optional[str] = None) -> Tuple[int, str, str]:
    """Execute Redis command"""
    try:
        cmd = ['redis-cli', '-h', host, '-p', str(port)]
        if password:
            cmd.extend(['-a', password])
        cmd.extend(command.split())
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "Redis CLI not found. Install with: brew install redis"
    except subprocess.TimeoutExpired:
        return 1, "", "Command timeout"
    except Exception as e:
        return 1, "", str(e)


def execute_sqlite_query(db_path: str, query: str) -> Tuple[int, str, str]:
    """Execute SQLite query"""
    try:
        cmd = ['sqlite3', db_path, query]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "SQLite3 not found (usually pre-installed on macOS)"
    except subprocess.TimeoutExpired:
        return 1, "", "Query timeout"
    except Exception as e:
        return 1, "", str(e)
