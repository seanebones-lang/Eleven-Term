#!/usr/bin/env python3
"""
API Utilities for NextEleven Terminal Agent
Provides enhanced API testing capabilities
"""

import subprocess
import json
import os
from typing import Dict, Any, Tuple, Optional
from pathlib import Path


def httpie_request(method: str, url: str, headers: Optional[Dict[str, str]] = None, 
                   data: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None) -> Tuple[int, str, str]:
    """Execute HTTP request using HTTPie"""
    try:
        cmd = ['http', method.upper(), url]
        
        # Add headers
        if headers:
            for key, value in headers.items():
                cmd.append(f'{key}:{value}')
        
        # Add JSON data
        if json_data:
            cmd.append('Content-Type:application/json')
            cmd.append(json.dumps(json_data))
        elif data:
            # Form data
            for key, value in data.items():
                cmd.append(f'{key}={value}')
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "HTTPie not found. Install with: brew install httpie"
    except subprocess.TimeoutExpired:
        return 1, "", "Request timeout"
    except Exception as e:
        return 1, "", str(e)


def curl_request(method: str, url: str, headers: Optional[Dict[str, str]] = None,
                 data: Optional[str] = None, json_data: Optional[Dict[str, Any]] = None) -> Tuple[int, str, str]:
    """Execute HTTP request using curl (enhanced wrapper)"""
    try:
        cmd = ['curl', '-X', method.upper(), '-s', '-w', '\n%{http_code}', url]
        
        # Add headers
        if headers:
            for key, value in headers.items():
                cmd.extend(['-H', f'{key}: {value}'])
        
        # Add JSON data
        if json_data:
            cmd.extend(['-H', 'Content-Type: application/json'])
            cmd.extend(['-d', json.dumps(json_data)])
        elif data:
            cmd.extend(['-d', data])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        # Parse output (separate body and status code)
        output_lines = result.stdout.split('\n')
        if len(output_lines) > 1:
            status_code = output_lines[-1]
            body = '\n'.join(output_lines[:-1])
        else:
            status_code = str(result.returncode) if result.returncode != 0 else "200"
            body = result.stdout
        
        return result.returncode, body, result.stderr + f"\nStatus: {status_code}"
    except FileNotFoundError:
        return 1, "", "curl not found (usually pre-installed)"
    except subprocess.TimeoutExpired:
        return 1, "", "Request timeout"
    except Exception as e:
        return 1, "", str(e)
