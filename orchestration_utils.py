#!/usr/bin/env python3
"""
Container Orchestration Utilities for NextEleven Terminal Agent
Provides Kubernetes and container orchestration capabilities
"""

import subprocess
import json
import os
from typing import Dict, Any, Tuple, Optional, List


def kubectl_get(resource: str, namespace: Optional[str] = None, output_format: str = "json") -> Tuple[int, str, str]:
    """Get Kubernetes resources"""
    try:
        cmd = ['kubectl', 'get', resource, '-o', output_format]
        if namespace:
            cmd.extend(['-n', namespace])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "kubectl not found. Install with: brew install kubectl"
    except subprocess.TimeoutExpired:
        return 1, "", "kubectl timeout"
    except Exception as e:
        return 1, "", str(e)


def kubectl_apply(file_path: str, namespace: Optional[str] = None) -> Tuple[int, str, str]:
    """Apply Kubernetes manifest"""
    try:
        cmd = ['kubectl', 'apply', '-f', file_path]
        if namespace:
            cmd.extend(['-n', namespace])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "kubectl not found"
    except subprocess.TimeoutExpired:
        return 1, "", "kubectl timeout"
    except Exception as e:
        return 1, "", str(e)


def kubectl_delete(resource: str, name: str, namespace: Optional[str] = None) -> Tuple[int, str, str]:
    """Delete Kubernetes resource"""
    try:
        cmd = ['kubectl', 'delete', resource, name]
        if namespace:
            cmd.extend(['-n', namespace])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "kubectl not found"
    except subprocess.TimeoutExpired:
        return 1, "", "kubectl timeout"
    except Exception as e:
        return 1, "", str(e)


def helm_list(namespace: Optional[str] = None) -> Tuple[int, str, str]:
    """List Helm releases"""
    try:
        cmd = ['helm', 'list', '--output', 'json']
        if namespace:
            cmd.extend(['-n', namespace])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "helm not found. Install with: brew install helm"
    except subprocess.TimeoutExpired:
        return 1, "", "helm timeout"
    except Exception as e:
        return 1, "", str(e)


def helm_install(name: str, chart: str, namespace: Optional[str] = None, values_file: Optional[str] = None) -> Tuple[int, str, str]:
    """Install Helm chart"""
    try:
        cmd = ['helm', 'install', name, chart]
        if namespace:
            cmd.extend(['-n', namespace, '--create-namespace'])
        if values_file:
            cmd.extend(['-f', values_file])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "helm not found"
    except subprocess.TimeoutExpired:
        return 1, "", "helm timeout"
    except Exception as e:
        return 1, "", str(e)


def helm_upgrade(name: str, chart: str, namespace: Optional[str] = None, values_file: Optional[str] = None) -> Tuple[int, str, str]:
    """Upgrade Helm release"""
    try:
        cmd = ['helm', 'upgrade', name, chart]
        if namespace:
            cmd.extend(['-n', namespace])
        if values_file:
            cmd.extend(['-f', values_file])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "helm not found"
    except subprocess.TimeoutExpired:
        return 1, "", "helm timeout"
    except Exception as e:
        return 1, "", str(e)


def docker_compose_up(compose_file: Optional[str] = None, services: Optional[List[str]] = None, detach: bool = True) -> Tuple[int, str, str]:
    """Start Docker Compose services"""
    try:
        cmd = ['docker-compose']
        if compose_file:
            cmd.extend(['-f', compose_file])
        cmd.append('up')
        if detach:
            cmd.append('-d')
        if services:
            cmd.extend(services)
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "docker-compose not found. Install with: brew install docker-compose"
    except subprocess.TimeoutExpired:
        return 1, "", "docker-compose timeout"
    except Exception as e:
        return 1, "", str(e)


def docker_compose_down(compose_file: Optional[str] = None) -> Tuple[int, str, str]:
    """Stop Docker Compose services"""
    try:
        cmd = ['docker-compose']
        if compose_file:
            cmd.extend(['-f', compose_file])
        cmd.append('down')
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "docker-compose not found"
    except subprocess.TimeoutExpired:
        return 1, "", "docker-compose timeout"
    except Exception as e:
        return 1, "", str(e)


def docker_compose_ps(compose_file: Optional[str] = None) -> Tuple[int, str, str]:
    """List Docker Compose services status"""
    try:
        cmd = ['docker-compose']
        if compose_file:
            cmd.extend(['-f', compose_file])
        cmd.append('ps')
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "docker-compose not found"
    except subprocess.TimeoutExpired:
        return 1, "", "docker-compose timeout"
    except Exception as e:
        return 1, "", str(e)
