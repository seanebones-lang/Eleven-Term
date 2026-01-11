#!/usr/bin/env python3
"""
Sudo Utilities for Automatic Sudo Access
Provides seamless sudo access for accessibility needs
"""

import subprocess
import os
import sys
from typing import Optional, Tuple
import getpass

def get_sudo_password_from_keychain() -> Optional[str]:
    """Retrieve sudo password from macOS Keychain"""
    try:
        result = subprocess.run(
            ['security', 'find-generic-password', '-s', 'grok-terminal', '-a', 'sudo-password', '-w'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def store_sudo_password_in_keychain(password: str) -> bool:
    """Store sudo password securely in macOS Keychain"""
    try:
        # Delete existing password if it exists
        subprocess.run(
            ['security', 'delete-generic-password', '-s', 'grok-terminal', '-a', 'sudo-password'],
            capture_output=True,
            stderr=subprocess.DEVNULL
        )
        
        # Add new password
        proc = subprocess.Popen(
            ['security', 'add-generic-password', '-s', 'grok-terminal', '-a', 'sudo-password', '-w', password, '-U'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        proc.communicate()
        return proc.returncode == 0
    except Exception:
        return False

def prompt_for_sudo_password() -> Optional[str]:
    """Prompt user for sudo password (one-time setup)"""
    try:
        password = getpass.getpass("Enter your sudo password (stored securely in Keychain): ")
        if password and store_sudo_password_in_keychain(password):
            print("✓ Sudo password stored securely in Keychain")
            return password
        return None
    except (KeyboardInterrupt, EOFError):
        return None

def check_if_sudo_needed(command: str, result: subprocess.CompletedProcess) -> bool:
    """Check if a command failed due to permission issues requiring sudo"""
    if result.returncode == 0:
        return False
    
    # Check stderr for permission errors
    stderr_lower = result.stderr.lower()
    permission_indicators = [
        'permission denied',
        'operation not permitted',
        'access denied',
        'cannot open',
        'read-only file system',
        'eacces',
        'eperm'
    ]
    
    for indicator in permission_indicators:
        if indicator in stderr_lower:
            return True
    
    return False

def execute_with_auto_sudo(cmd: str, allow_force: bool = False, timeout: int = 60, auto_sudo: bool = True) -> subprocess.CompletedProcess:
    """
    Execute command with automatic sudo when needed (for accessibility)
    
    Args:
        cmd: Command to execute
        allow_force: Whether --force flag was provided
        timeout: Command timeout
        auto_sudo: Whether to automatically use sudo when needed
        
    Returns:
        CompletedProcess with result
    """
    from security_utils import execute_command_safely, SecurityError
    
    # First, try without sudo (but disable auto_sudo to avoid recursion)
    try:
        result = execute_command_safely(cmd, allow_force=allow_force, timeout=timeout, auto_sudo=False)
        
        # If successful, return result
        if result.returncode == 0:
            return result
        
        # If failed and auto_sudo is enabled, check if sudo is needed
        if auto_sudo and check_if_sudo_needed(cmd, result):
            # Get sudo password from Keychain
            sudo_password = get_sudo_password_from_keychain()
            
            if not sudo_password:
                # Prompt once and store (for accessibility - one-time setup)
                print("🔐 Sudo access needed. Enter your password once (stored securely in Keychain):")
                sudo_password = prompt_for_sudo_password()
                if not sudo_password:
                    return result  # Return original failure
            
            # Retry with sudo
            sudo_cmd = f"sudo -S {cmd}"
            try:
                proc = subprocess.Popen(
                    sudo_cmd,
                    shell=True,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=timeout
                )
                stdout, stderr = proc.communicate(input=f"{sudo_password}\n", timeout=timeout)
                
                result = subprocess.CompletedProcess(
                    args=sudo_cmd.split(),
                    returncode=proc.returncode,
                    stdout=stdout,
                    stderr=stderr
                )
                
                # If sudo worked, return the result
                if result.returncode == 0:
                    return result
                else:
                    # Sudo might have failed (wrong password, etc.)
                    # Check if password is wrong
                    if 'sorry' in stderr.lower() or 'incorrect password' in stderr.lower() or 'try again' in stderr.lower():
                        # Password might be wrong, prompt again
                        print("⚠️  Password incorrect. Please re-enter:")
                        new_password = prompt_for_sudo_password()
                        if new_password:
                            # Retry once more
                            proc = subprocess.Popen(
                                sudo_cmd,
                                shell=True,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True,
                                timeout=timeout
                            )
                            stdout, stderr = proc.communicate(input=f"{new_password}\n", timeout=timeout)
                            return subprocess.CompletedProcess(
                                args=sudo_cmd.split(),
                                returncode=proc.returncode,
                                stdout=stdout,
                                stderr=stderr
                            )
                    
                    return result
            except subprocess.TimeoutExpired:
                proc.kill()
                raise
            except Exception as e:
                # If sudo execution fails, return original result
                return result
        
        return result
    except SecurityError:
        # Security validation failed, don't try sudo
        raise
    except Exception as e:
        # Other errors, return failure
        return subprocess.CompletedProcess(
            args=cmd.split() if isinstance(cmd, str) else cmd,
            returncode=1,
            stdout="",
            stderr=str(e)
        )
