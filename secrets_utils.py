#!/usr/bin/env python3
"""
Secrets Management Utilities for NextEleven Terminal Agent
Provides secure secrets management capabilities
"""

import subprocess
import json
import os
from typing import Dict, Any, Tuple, Optional


def vault_read(path: str, field: Optional[str] = None) -> Tuple[int, str, str]:
    """Read secret from Vault"""
    try:
        cmd = ['vault', 'kv', 'get', '-format=json', path]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and field:
            try:
                data = json.loads(result.stdout)
                value = data.get('data', {}).get('data', {}).get(field, '')
                return 0, value, ""
            except (json.JSONDecodeError, KeyError):
                pass
        
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "vault not found. Install with: brew install vault"
    except subprocess.TimeoutExpired:
        return 1, "", "vault timeout"
    except Exception as e:
        return 1, "", str(e)


def vault_write(path: str, data: Dict[str, str]) -> Tuple[int, str, str]:
    """Write secret to Vault"""
    try:
        # Vault write expects key=value pairs
        cmd = ['vault', 'kv', 'put', path]
        for key, value in data.items():
            cmd.append(f"{key}={value}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "vault not found"
    except subprocess.TimeoutExpired:
        return 1, "", "vault timeout"
    except Exception as e:
        return 1, "", str(e)


def vault_list(path: str) -> Tuple[int, str, str]:
    """List secrets in Vault path"""
    try:
        cmd = ['vault', 'kv', 'list', path]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "vault not found"
    except subprocess.TimeoutExpired:
        return 1, "", "vault timeout"
    except Exception as e:
        return 1, "", str(e)


def sops_decrypt(file_path: str, output_file: Optional[str] = None) -> Tuple[int, str, str]:
    """Decrypt file with SOPS"""
    try:
        cmd = ['sops', '-d', file_path]
        if output_file:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                with open(output_file, 'w') as f:
                    f.write(result.stdout)
                return 0, f"Decrypted to {output_file}", ""
            return result.returncode, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "sops not found. Install with: brew install sops"
    except subprocess.TimeoutExpired:
        return 1, "", "sops timeout"
    except Exception as e:
        return 1, "", str(e)


def sops_encrypt(file_path: str, output_file: Optional[str] = None) -> Tuple[int, str, str]:
    """Encrypt file with SOPS"""
    try:
        output_file = output_file or file_path + ".enc"
        cmd = ['sops', '-e', file_path]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            with open(output_file, 'w') as f:
                f.write(result.stdout)
            return 0, f"Encrypted to {output_file}", ""
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "sops not found"
    except subprocess.TimeoutExpired:
        return 1, "", "sops timeout"
    except Exception as e:
        return 1, "", str(e)
