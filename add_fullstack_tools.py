#!/usr/bin/env python3
"""
Script to add database and API tools to grok_agent.py
This will insert tool functions and update the TOOLS registry
"""

import re

# Read grok_agent.py
with open('grok_agent.py', 'r') as f:
    content = f.read()
    lines = content.split('\n')

# Find insertion point (before TOOLS registry)
tools_registry_line = None
for i, line in enumerate(lines):
    if 'TOOLS = {' in line and not line.strip().startswith('#'):
        tools_registry_line = i
        break

if not tools_registry_line:
    print("ERROR: Could not find TOOLS registry")
    exit(1)

print(f"Found TOOLS registry at line {tools_registry_line + 1}")
print(f"Will insert database and API tools before line {tools_registry_line + 1}")

# Database and API tool functions to add
database_api_tools = '''
# Database Tools
def tool_mysql_query(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Execute MySQL query"""
    try:
        from database_utils import execute_mysql_query
        host = params.get('host', 'localhost')
        user = params.get('user', 'root')
        database = params.get('database', '')
        query = params.get('query', '')
        password = params.get('password', None)
        
        if not database or not query:
            return 1, "", "database and query parameters required"
        
        return execute_mysql_query(host, user, database, query, password)
    except ImportError:
        return 1, "", "database_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_postgresql_query(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Execute PostgreSQL query"""
    try:
        from database_utils import execute_postgresql_query
        host = params.get('host', 'localhost')
        user = params.get('user', 'postgres')
        database = params.get('database', '')
        query = params.get('query', '')
        password = params.get('password', None)
        
        if not database or not query:
            return 1, "", "database and query parameters required"
        
        return execute_postgresql_query(host, user, database, query, password)
    except ImportError:
        return 1, "", "database_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_mongodb_query(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Execute MongoDB query"""
    try:
        from database_utils import execute_mongodb_query
        uri = params.get('uri', 'mongodb://localhost:27017')
        database = params.get('database', '')
        collection = params.get('collection', '')
        query = params.get('query', '')
        
        if not database or not collection or not query:
            return 1, "", "database, collection, and query parameters required"
        
        return execute_mongodb_query(uri, database, collection, query)
    except ImportError:
        return 1, "", "database_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_redis_command(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Execute Redis command"""
    try:
        from database_utils import execute_redis_command
        host = params.get('host', 'localhost')
        port = params.get('port', 6379)
        command = params.get('command', '')
        password = params.get('password', None)
        
        if not command:
            return 1, "", "command parameter required"
        
        return execute_redis_command(host, port, command, password)
    except ImportError:
        return 1, "", "database_utils module not available"
    except Exception as e:
        return 1, "", str(e)

# API Tools
def tool_httpie_request(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Execute HTTP request using HTTPie"""
    try:
        from api_utils import httpie_request
        method = params.get('method', 'GET')
        url = params.get('url', '')
        headers = params.get('headers', None)
        data = params.get('data', None)
        json_data = params.get('json', None)
        
        if not url:
            return 1, "", "url parameter required"
        
        return httpie_request(method, url, headers, data, json_data)
    except ImportError:
        return 1, "", "api_utils module not available"
    except Exception as e:
        return 1, "", str(e)

def tool_curl_request(params: Dict[str, Any]) -> Tuple[int, str, str]:
    """Execute HTTP request using curl (enhanced)"""
    try:
        from api_utils import curl_request
        method = params.get('method', 'GET')
        url = params.get('url', '')
        headers = params.get('headers', None)
        data = params.get('data', None)
        json_data = params.get('json', None)
        
        if not url:
            return 1, "", "url parameter required"
        
        return curl_request(method, url, headers, data, json_data)
    except ImportError:
        return 1, "", "api_utils module not available"
    except Exception as e:
        return 1, "", str(e)
'''

print("\nTool functions to add:")
print(database_api_tools[:200] + "...")

# We'll do this manually with search_replace instead
print("\nNote: This script identifies the location. Manual insertion recommended.")
