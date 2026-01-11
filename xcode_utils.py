#!/usr/bin/env python3
"""
Xcode Utilities for NextEleven Terminal Agent
Provides tools for working with Xcode projects and files
"""

import os
import subprocess
import json
import plistlib
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import re

def find_xcode_project(path: str = ".") -> Optional[str]:
    """Find Xcode project (.xcodeproj) or workspace (.xcworkspace) in directory"""
    path_obj = Path(path).expanduser().resolve()
    
    # Search for .xcodeproj
    for xcodeproj in path_obj.rglob("*.xcodeproj"):
        return str(xcodeproj)
    
    # Search for .xcworkspace
    for xcworkspace in path_obj.rglob("*.xcworkspace"):
        return str(xcworkspace)
    
    return None

def read_xcode_project_info(project_path: str) -> Dict[str, Any]:
    """Read basic information about Xcode project"""
    project_path = Path(project_path).expanduser().resolve()
    
    info = {
        "project_path": str(project_path),
        "exists": False,
        "type": None,
        "name": None,
        "schemes": [],
        "targets": [],
        "error": None
    }
    
    if not project_path.exists():
        info["error"] = f"Project not found: {project_path}"
        return info
    
    info["exists"] = True
    
    # Determine project type
    if project_path.suffix == ".xcodeproj":
        info["type"] = "project"
        info["name"] = project_path.stem
        pbxproj_path = project_path / "project.pbxproj"
        
        if pbxproj_path.exists():
            # Try to read basic info from pbxproj
            try:
                with open(pbxproj_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Extract targets (simplified)
                    targets = re.findall(r'buildConfigurationList.*=.*PBXNativeTarget.*name = (.*?);', content)
                    info["targets"] = [t.strip('"').strip() for t in targets[:10]]  # Limit to 10
            except Exception as e:
                info["error"] = f"Error reading pbxproj: {e}"
    elif project_path.suffix == ".xcworkspace":
        info["type"] = "workspace"
        info["name"] = project_path.stem
    
    # Try to get schemes using xcodebuild
    try:
        if info["type"] == "workspace":
            result = subprocess.run(
                ['xcodebuild', '-list', '-workspace', str(project_path)],
                capture_output=True,
                text=True,
                timeout=10
            )
        else:
            result = subprocess.run(
                ['xcodebuild', '-list', '-project', str(project_path)],
                capture_output=True,
                text=True,
                timeout=10
            )
        
        if result.returncode == 0:
            # Parse schemes from output
            lines = result.stdout.split('\n')
            in_schemes = False
            for line in lines:
                if 'Schemes:' in line:
                    in_schemes = True
                    continue
                if in_schemes and line.strip() and not line.startswith(' '):
                    if ':' in line or line.strip() == '':
                        in_schemes = False
                        continue
                    scheme = line.strip()
                    if scheme:
                        info["schemes"].append(scheme)
    except Exception:
        pass  # xcodebuild might not be available
    
    return info

def list_xcode_files(project_path: str, file_type: str = "all") -> List[str]:
    """List source files in Xcode project"""
    project_path = Path(project_path).expanduser().resolve()
    files = []
    
    if project_path.suffix == ".xcodeproj":
        pbxproj_path = project_path / "project.pbxproj"
        if pbxproj_path.exists():
            try:
                with open(pbxproj_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Extract file paths (simplified pattern matching)
                    # Look for file references
                    patterns = {
                        "swift": r'\.(swift)\s*=.*path = (.*?);',
                        "objc": r'\.(m|h|mm|hpp|cpp)\s*=.*path = (.*?);',
                        "all": r'path = (.*?);'
                    }
                    
                    pattern = patterns.get(file_type, patterns["all"])
                    matches = re.findall(pattern, content)
                    
                    for match in matches:
                        if isinstance(match, tuple):
                            file_path = match[1] if len(match) > 1 else match[0]
                        else:
                            file_path = match
                        
                        file_path = file_path.strip('"').strip()
                        if file_path:
                            # Make path relative to project
                            full_path = project_path.parent / file_path
                            if full_path.exists():
                                files.append(str(full_path))
            except Exception:
                pass
    
    # Also search in typical source directories
    project_dir = project_path.parent
    source_dirs = ["Sources", "src", "Source", "Classes", "App"]
    
    extensions = {
        "swift": [".swift"],
        "objc": [".m", ".h", ".mm", ".hpp", ".cpp"],
        "all": [".swift", ".m", ".h", ".mm", ".hpp", ".cpp", ".xib", ".storyboard"]
    }
    
    ext_list = extensions.get(file_type, extensions["all"])
    
    for source_dir in source_dirs:
        src_path = project_dir / source_dir
        if src_path.exists() and src_path.is_dir():
            for ext in ext_list:
                for file_path in src_path.rglob(f"*{ext}"):
                    if str(file_path) not in files:
                        files.append(str(file_path))
    
    # Search root directory too
    for ext in ext_list:
        for file_path in project_dir.rglob(f"*{ext}"):
            if file_path.parent != project_path.parent or file_path.suffix in ext_list:
                if str(file_path) not in files:
                    files.append(str(file_path))
    
    return sorted(files)[:100]  # Limit to 100 files

def read_xcode_file(file_path: str) -> Tuple[int, str, str]:
    """Read Xcode source file (Swift, Objective-C, etc.)"""
    try:
        file_path_obj = Path(file_path).expanduser().resolve()
        if not file_path_obj.exists():
            return 1, "", f"File not found: {file_path}"
        
        with open(file_path_obj, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        return 0, content, ""
    except Exception as e:
        return 1, "", str(e)

def write_xcode_file(file_path: str, content: str) -> Tuple[int, str, str]:
    """Write content to Xcode source file"""
    try:
        file_path_obj = Path(file_path).expanduser().resolve()
        
        # Create directory if it doesn't exist
        file_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path_obj, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return 0, f"Written to {file_path}", ""
    except Exception as e:
        return 1, "", str(e)

def build_xcode_project(project_path: str, scheme: Optional[str] = None, configuration: str = "Debug") -> Tuple[int, str, str]:
    """Build Xcode project using xcodebuild"""
    try:
        project_path_obj = Path(project_path).expanduser().resolve()
        
        if not project_path_obj.exists():
            return 1, "", f"Project not found: {project_path}"
        
        cmd = ['xcodebuild']
        
        if project_path_obj.suffix == ".xcworkspace":
            cmd.extend(['-workspace', str(project_path_obj)])
        else:
            cmd.extend(['-project', str(project_path_obj)])
        
        if scheme:
            cmd.extend(['-scheme', scheme])
        
        cmd.extend(['-configuration', configuration])
        cmd.append('build')
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd=project_path_obj.parent
        )
        
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Build timed out after 5 minutes"
    except Exception as e:
        return 1, "", str(e)

def open_xcode_project(project_path: str) -> Tuple[int, str, str]:
    """Open Xcode project in Xcode app"""
    try:
        project_path_obj = Path(project_path).expanduser().resolve()
        
        if not project_path_obj.exists():
            return 1, "", f"Project not found: {project_path}"
        
        result = subprocess.run(
            ['open', str(project_path_obj)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        return result.returncode, f"Opened {project_path} in Xcode", result.stderr
    except Exception as e:
        return 1, "", str(e)
