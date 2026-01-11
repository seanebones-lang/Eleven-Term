#!/usr/bin/env python3
"""
Security Utilities for NextEleven Terminal Agent
Provides safe command execution, input sanitization, and validation
"""

import re
import shlex
import subprocess
import sys
from typing import Tuple, Optional
from pathlib import Path

# Dangerous command patterns that require --force flag
DANGEROUS_PATTERNS = [
    r'\brm\s+-rf\b',
    r'\bsudo\s+',
    r'\bkill\s+-9\b',
    r'\bmkfs\b',
    r'\bdd\s+if=',
    r'\bchmod\s+777\b',
    r'\>\s*/dev/',
    r'\bformat\b',
    r'\bfdisk\b',
    r'\bdel\s+/f\b',
    r'\bwget\s+.*\|\s*sh\b',  # Download and execute
    r'\bcurl\s+.*\|\s*sh\b',  # Download and execute
]

# Allowed command whitelist (optional, can be disabled)
# If enabled, only these commands can be executed
ALLOWED_COMMANDS_WHITELIST = None  # Set to list of commands to enable whitelist mode

# Maximum command length to prevent buffer overflow attacks
MAX_COMMAND_LENGTH = 10000


class SecurityError(Exception):
    """Raised when a security validation fails"""
    pass


def sanitize_input(text: str, max_length: int = MAX_COMMAND_LENGTH) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
        
    Raises:
        SecurityError: If input is invalid or too long
    """
    if not isinstance(text, str):
        raise SecurityError("Input must be a string")
    
    if len(text) > max_length:
        raise SecurityError(f"Input too long (max {max_length} characters)")
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Remove control characters except newline, tab, carriage return
    # Preserve whitespace characters: \n (newline), \t (tab), \r (carriage return)
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t\r')
    
    # Don't strip if we want to preserve newlines/tabs at the end
    # But still trim leading/trailing spaces (not newlines/tabs)
    text = text.rstrip(' ')  # Only strip trailing spaces, not newlines/tabs
    text = text.lstrip(' ')  # Only strip leading spaces, not newlines/tabs
    
    return text


def is_creator_verified() -> bool:
    """Check if creator identity is verified"""
    try:
        from identity_verify import is_creator_verified as check_creator
        return check_creator()
    except ImportError:
        return False

def validate_command_structure(cmd: str, allow_force: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Validate command structure for security issues.
    Verified creator can override all restrictions.
    
    Args:
        cmd: Command to validate
        allow_force: Whether --force flag was provided
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Creator override: Verified creator can bypass all restrictions
    creator_verified = is_creator_verified()
    
    if not cmd or not cmd.strip():
        if creator_verified:
            return True, None  # Creator can execute empty commands if needed
        return False, "Empty command not allowed"
    
    # Check length
    if len(cmd) > MAX_COMMAND_LENGTH:
        if creator_verified:
            return True, None  # Creator override
        return False, f"Command too long (max {MAX_COMMAND_LENGTH} characters)"
    
    cmd_lower = cmd.lower()
    
    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd_lower):
            if creator_verified:
                return True, None  # Creator override - all restrictions bypassed
            if not allow_force:
                return False, f"Dangerous command pattern detected: {pattern}"
            # Even with --force, we still block system-destructive commands
            # Block commands that target root or system directories
            if re.search(r'\s+/(?:\s|$)', cmd_lower) or cmd_lower.strip() == '/':
                if creator_verified:
                    return True, None  # Creator override
                return False, "System-destructive commands are not allowed even with --force"
            # Even with --force, log the dangerous command
            # (could add audit logging here)
    
    # Check for command injection attempts
    injection_patterns = [
        r';\s*(rm|del|format|mkfs|dd)',
        r'&&\s*(rm|del|format|mkfs|dd)',
        r'\|\s*(rm|del|format|mkfs|dd)',
        r'`.*(rm|del|format|mkfs|dd)',
        r'\$\(.*(rm|del|format|mkfs|dd)',
        r'\$\{.*(rm|del|format|mkfs|dd)',
    ]
    
    for pattern in injection_patterns:
        if re.search(pattern, cmd_lower):
            if creator_verified:
                return True, None  # Creator override
            return False, f"Command injection pattern detected: {pattern}"
    
    # Check for whitelist if enabled
    if ALLOWED_COMMANDS_WHITELIST is not None:
        # Extract first command
        first_word = cmd.split()[0] if cmd.split() else ""
        if first_word not in ALLOWED_COMMANDS_WHITELIST:
            if creator_verified:
                return True, None  # Creator override
            return False, f"Command not in whitelist: {first_word}"
    
    return True, None


def sanitize_command(cmd: str) -> str:
    """
    Sanitize a command string before execution.
    
    Args:
        cmd: Command string to sanitize
        
    Returns:
        Sanitized command string
    """
    # First sanitize input
    cmd = sanitize_input(cmd)
    
    # Remove any embedded null bytes
    cmd = cmd.replace('\x00', '')
    
    # Trim whitespace
    cmd = cmd.strip()
    
    return cmd


def execute_command_safely(cmd: str, allow_force: bool = False, timeout: int = 60, auto_sudo: bool = True) -> subprocess.CompletedProcess:
    """
    Execute a command safely with validation and sanitization.
    
    Args:
        cmd: Command to execute
        allow_force: Whether --force flag was provided
        timeout: Command timeout in seconds
        
    Returns:
        CompletedProcess with stdout, stderr, returncode
        
    Raises:
        SecurityError: If command fails security validation
        subprocess.TimeoutExpired: If command times out
        subprocess.SubprocessError: If execution fails
    """
    # Step 1: Sanitize input
    try:
        cmd = sanitize_command(cmd)
    except SecurityError as e:
        raise SecurityError(f"Command sanitization failed: {e}")
    
    # Step 2: Validate command structure
    is_valid, error_msg = validate_command_structure(cmd, allow_force)
    if not is_valid:
        raise SecurityError(f"Command validation failed: {error_msg}")
    
    # Step 3: Execute safely
    # For simple commands (no pipes/redirects), use shell=False for maximum safety
    # For complex commands, we need shell=True but with validation already done
    
    has_shell_operators = bool(re.search(r'[|&;<>]', cmd))
    
    if has_shell_operators:
        # Complex command with pipes/redirects - use shell=True but we've validated it
        # This is still safer than eval because:
        # 1. We've sanitized the input
        # 2. We've validated against dangerous patterns
        # 3. We use subprocess which has better isolation than eval
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=Path.cwd(),  # Execute in current directory
            )
            # Step 4: Auto-sudo if needed (for accessibility)
            if auto_sudo and result.returncode != 0:
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
                needs_sudo = any(indicator in stderr_lower for indicator in permission_indicators)
                
                if needs_sudo:
                    try:
                        from sudo_utils import execute_with_auto_sudo
                        return execute_with_auto_sudo(cmd, allow_force=allow_force, timeout=timeout, auto_sudo=True)
                    except ImportError:
                        pass  # sudo_utils not available
            
            return result
        except subprocess.TimeoutExpired as e:
            raise
        except Exception as e:
            raise SecurityError(f"Command execution failed: {e}")
    else:
        # Simple command - split and execute with shell=False (safer)
        try:
            args = shlex.split(cmd)
            if not args:
                raise SecurityError("Empty command after parsing")
            
            result = subprocess.run(
                args,
                shell=False,  # Maximum safety - no shell interpretation
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=Path.cwd(),
            )
            # Step 4: Auto-sudo if needed (for accessibility)
            if auto_sudo and result.returncode != 0:
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
                needs_sudo = any(indicator in stderr_lower for indicator in permission_indicators)
                
                if needs_sudo:
                    try:
                        from sudo_utils import execute_with_auto_sudo
                        return execute_with_auto_sudo(cmd, allow_force=allow_force, timeout=timeout, auto_sudo=True)
                    except ImportError:
                        pass  # sudo_utils not available
            
            return result
        except FileNotFoundError as e:
            # Command not found - this is not a security error, just a runtime error
            # Return error result instead of raising SecurityError
            result = subprocess.CompletedProcess(
                args=args,
                returncode=127,  # Command not found
                stdout="",
                stderr=str(e)
            )
            return result
        except ValueError as e:
            # If shlex.split fails, it might be a complex command we didn't catch
            # Fall back to shell execution with full validation already done
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=Path.cwd(),
            )
            # Step 4: Auto-sudo if needed (for accessibility)
            if auto_sudo and result.returncode != 0:
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
                needs_sudo = any(indicator in stderr_lower for indicator in permission_indicators)
                
                if needs_sudo:
                    try:
                        from sudo_utils import execute_with_auto_sudo
                        return execute_with_auto_sudo(cmd, allow_force=allow_force, timeout=timeout, auto_sudo=True)
                    except ImportError:
                        pass  # sudo_utils not available
            
            return result
        except subprocess.TimeoutExpired as e:
            raise
        except Exception as e:
            raise SecurityError(f"Command execution failed: {e}")


def main():
    """
    CLI interface for safe command execution.
    Usage: security_utils.py <command> [--force]
    """
    if len(sys.argv) < 2:
        print("Usage: security_utils.py <command> [--force]", file=sys.stderr)
        sys.exit(1)
    
    cmd = sys.argv[1]
    allow_force = '--force' in sys.argv
    
    try:
        result = execute_command_safely(cmd, allow_force)
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        sys.exit(result.returncode)
    except SecurityError as e:
        print(f"SECURITY_ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("ERROR: Command timed out", file=sys.stderr)
        sys.exit(124)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
