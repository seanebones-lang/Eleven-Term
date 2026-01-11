#!/usr/bin/env python3
"""
Android Utilities for NextEleven Terminal Agent
Provides comprehensive tools for working with Android Studio and all its components
"""

import os
import subprocess
import json
import shutil
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import re
import platform

def find_android_project(path: str = ".") -> Optional[str]:
    """Find Android Studio project in directory"""
    path_obj = Path(path).expanduser().resolve()
    
    # Search for AndroidManifest.xml (Android project indicator)
    for manifest in path_obj.rglob("AndroidManifest.xml"):
        # Check if it's in a typical Android project structure
        project_dir = manifest.parent.parent.parent  # Usually app/src/main/AndroidManifest.xml
        if (project_dir / "build.gradle").exists() or (project_dir.parent / "build.gradle").exists():
            return str(project_dir.parent if (project_dir / "build.gradle").exists() else project_dir)
    
    # Search for build.gradle in root
    for gradle_file in path_obj.rglob("build.gradle"):
        if "settings.gradle" in [f.name for f in gradle_file.parent.iterdir()]:
            return str(gradle_file.parent)
    
    # Search for settings.gradle (Android/Gradle project)
    for settings in path_obj.rglob("settings.gradle"):
        return str(settings.parent)
    
    return None

def read_android_project_info(project_path: str) -> Dict[str, Any]:
    """Read basic information about Android project"""
    project_path = Path(project_path).expanduser().resolve()
    
    info = {
        "project_path": str(project_path),
        "exists": False,
        "type": None,
        "name": None,
        "package_name": None,
        "min_sdk": None,
        "target_sdk": None,
        "modules": [],
        "error": None
    }
    
    if not project_path.exists():
        info["error"] = f"Project not found: {project_path}"
        return info
    
    info["exists"] = True
    info["type"] = "android"
    info["name"] = project_path.name
    
    # Try to read build.gradle (Kotlin DSL or Groovy)
    build_gradle_path = project_path / "build.gradle"
    if not build_gradle_path.exists():
        build_gradle_path = project_path / "build.gradle.kts"
    
    if build_gradle_path.exists():
        try:
            with open(build_gradle_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Extract project name
                name_match = re.search(r'applicationId\s+["\']([^"\']+)["\']', content)
                if name_match:
                    info["package_name"] = name_match.group(1)
        except Exception:
            pass
    
    # Try to read app/build.gradle
    app_build_gradle = project_path / "app" / "build.gradle"
    if not app_build_gradle.exists():
        app_build_gradle = project_path / "app" / "build.gradle.kts"
    
    if app_build_gradle.exists():
        try:
            with open(app_build_gradle, 'r', encoding='utf-8') as f:
                content = f.read()
                # Extract minSdk and targetSdk
                min_sdk_match = re.search(r'minSdk\s+(?:Version)?\s*[=:]\s*(\d+)', content)
                if min_sdk_match:
                    info["min_sdk"] = int(min_sdk_match.group(1))
                
                target_sdk_match = re.search(r'targetSdk\s+(?:Version)?\s*[=:]\s*(\d+)', content)
                if target_sdk_match:
                    info["target_sdk"] = int(target_sdk_match.group(1))
                
                # Extract package name if not found
                if not info["package_name"]:
                    package_match = re.search(r'applicationId\s+["\']([^"\']+)["\']', content)
                    if package_match:
                        info["package_name"] = package_match.group(1)
        except Exception:
            pass
    
    # Find AndroidManifest.xml for package name
    manifest_path = project_path / "app" / "src" / "main" / "AndroidManifest.xml"
    if manifest_path.exists():
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                content = f.read()
                package_match = re.search(r'package=["\']([^"\']+)["\']', content)
                if package_match and not info["package_name"]:
                    info["package_name"] = package_match.group(1)
        except Exception:
            pass
    
    # List modules (directories with build.gradle)
    try:
        for item in project_path.iterdir():
            if item.is_dir():
                module_gradle = item / "build.gradle"
                if not module_gradle.exists():
                    module_gradle = item / "build.gradle.kts"
                if module_gradle.exists() and item.name != "build":
                    info["modules"].append(item.name)
    except Exception:
        pass
    
    return info

def list_android_files(project_path: str, file_type: str = "all") -> List[str]:
    """List source files in Android project"""
    project_path = Path(project_path).expanduser().resolve()
    files = []
    
    # Common Android source directories
    source_dirs = [
        "app/src/main/java",
        "app/src/main/kotlin",
        "app/src/main/java",
        "src/main/java",
        "src/main/kotlin"
    ]
    
    extensions = {
        "kotlin": [".kt", ".kts"],
        "java": [".java"],
        "xml": [".xml"],
        "all": [".kt", ".kts", ".java", ".xml", ".gradle"]
    }
    
    ext_list = extensions.get(file_type, extensions["all"])
    
    # Search in source directories
    for source_dir in source_dirs:
        src_path = project_path / source_dir
        if src_path.exists() and src_path.is_dir():
            for ext in ext_list:
                for file_path in src_path.rglob(f"*{ext}"):
                    if str(file_path) not in files:
                        files.append(str(file_path))
    
    # Also search in root and common directories
    common_dirs = ["app", "src", "libs"]
    for common_dir in common_dirs:
        common_path = project_path / common_dir
        if common_path.exists() and common_path.is_dir():
            for ext in ext_list:
                for file_path in common_path.rglob(f"*{ext}"):
                    if str(file_path) not in files:
                        files.append(str(file_path))
    
    return sorted(files)[:100]  # Limit to 100 files

def read_android_file(file_path: str) -> Tuple[int, str, str]:
    """Read Android source file (Kotlin, Java, XML, etc.)"""
    try:
        file_path_obj = Path(file_path).expanduser().resolve()
        if not file_path_obj.exists():
            return 1, "", f"File not found: {file_path}"
        
        with open(file_path_obj, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        return 0, content, ""
    except Exception as e:
        return 1, "", str(e)

def write_android_file(file_path: str, content: str) -> Tuple[int, str, str]:
    """Write content to Android source file"""
    try:
        file_path_obj = Path(file_path).expanduser().resolve()
        
        # Create directory if it doesn't exist
        file_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path_obj, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return 0, f"Written to {file_path}", ""
    except Exception as e:
        return 1, "", str(e)

def build_android_project(project_path: str, variant: Optional[str] = None, task: str = "assembleDebug") -> Tuple[int, str, str]:
    """Build Android project using Gradle"""
    try:
        project_path_obj = Path(project_path).expanduser().resolve()
        
        if not project_path_obj.exists():
            return 1, "", f"Project not found: {project_path}"
        
        # Check for gradlew (Gradle wrapper)
        gradlew = project_path_obj / "gradlew"
        if not gradlew.exists():
            gradlew = project_path_obj / "gradlew.bat"
        
        if gradlew.exists():
            cmd = [str(gradlew), task]
        else:
            # Fallback to system gradle
            cmd = ["gradle", task]
        
        if variant:
            cmd.append(f"-Pvariant={variant}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
            cwd=project_path_obj
        )
        
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Build timed out after 10 minutes"
    except Exception as e:
        return 1, "", str(e)

def find_android_studio() -> Optional[str]:
    """Find Android Studio installation"""
    # Check common locations
    common_paths = [
        "/Applications/Android Studio.app",
        "/Applications/AndroidStudio.app",
        "/opt/android-studio",
        os.path.expanduser("~/Applications/Android Studio.app"),
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    # Check PATH
    if shutil.which("studio"):
        return "studio"
    if shutil.which("android-studio"):
        return "android-studio"
    
    # Try to find via Spotlight on macOS
    if platform.system() == "Darwin":
        try:
            result = subprocess.run(
                ["mdfind", "kMDItemCFBundleIdentifier == 'com.google.android.studio'"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split('\n')[0]
        except Exception:
            pass
    
    return None

def get_android_home() -> Optional[str]:
    """Get Android SDK home directory"""
    # Check environment variable
    android_home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if android_home and os.path.exists(android_home):
        return android_home
    
    # Check common locations
    common_paths = [
        os.path.expanduser("~/Library/Android/sdk"),
        os.path.expanduser("~/Android/Sdk"),
        "/opt/android-sdk",
        "/usr/local/android-sdk",
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    return None

def get_android_studio_bin() -> Optional[str]:
    """Get Android Studio binary path"""
    studio_path = find_android_studio()
    if not studio_path:
        return None
    
    # If it's an .app bundle on macOS, use the Contents/MacOS/studio script
    if studio_path.endswith(".app"):
        bin_path = os.path.join(studio_path, "Contents", "MacOS", "studio")
        if os.path.exists(bin_path):
            return bin_path
        # Alternative: use Contents/bin/studio.sh
        bin_path = os.path.join(studio_path, "Contents", "bin", "studio.sh")
        if os.path.exists(bin_path):
            return bin_path
    
    return studio_path

def get_adb_path() -> Optional[str]:
    """Get ADB (Android Debug Bridge) path"""
    android_home = get_android_home()
    if android_home:
        adb_path = os.path.join(android_home, "platform-tools", "adb")
        if os.path.exists(adb_path):
            return adb_path
        # Try Windows path format
        adb_path = os.path.join(android_home, "platform-tools", "adb.exe")
        if os.path.exists(adb_path):
            return adb_path
    
    # Check PATH
    if shutil.which("adb"):
        return shutil.which("adb")
    
    return None

def get_emulator_path() -> Optional[str]:
    """Get Android emulator path"""
    android_home = get_android_home()
    if android_home:
        emulator_path = os.path.join(android_home, "emulator", "emulator")
        if os.path.exists(emulator_path):
            return emulator_path
        # Try Windows path format
        emulator_path = os.path.join(android_home, "emulator", "emulator.exe")
        if os.path.exists(emulator_path):
            return emulator_path
    
    # Check PATH
    if shutil.which("emulator"):
        return shutil.which("emulator")
    
    return None

def open_android_project(project_path: str) -> Tuple[int, str, str]:
    """Open Android Studio project in Android Studio app"""
    try:
        project_path_obj = Path(project_path).expanduser().resolve()
        
        if not project_path_obj.exists():
            return 1, "", f"Project not found: {project_path}"
        
        # Try multiple methods to open Android Studio
        
        # Method 1: Use 'open' command on macOS
        if platform.system() == "Darwin":
            try:
                result = subprocess.run(
                    ['open', '-a', 'Android Studio', str(project_path_obj)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    return 0, f"Opened {project_path} in Android Studio", ""
            except Exception:
                pass
            
            # Method 2: Use studio binary if available
            studio_bin = get_android_studio_bin()
            if studio_bin:
                try:
                    result = subprocess.Popen(
                        [studio_bin, str(project_path_obj)],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    return 0, f"Opening {project_path} in Android Studio", ""
                except Exception:
                    pass
        
        # Method 3: Use studio command if in PATH
        if shutil.which("studio"):
            try:
                result = subprocess.Popen(
                    ["studio", str(project_path_obj)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                return 0, f"Opening {project_path} in Android Studio", ""
            except Exception as e:
                return 1, "", f"Failed to open Android Studio: {str(e)}"
        
        return 1, "", "Android Studio not found. Please install Android Studio or add it to PATH."
    except Exception as e:
        return 1, "", str(e)

def list_android_emulators() -> Tuple[int, List[str], str]:
    """List available Android emulators"""
    try:
        emulator_path = get_emulator_path()
        if not emulator_path:
            return 1, [], "Android emulator not found. Please install Android SDK."
        
        result = subprocess.run(
            [emulator_path, "-list-avds"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return 1, [], result.stderr or "Failed to list emulators"
        
        emulators = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        return 0, emulators, ""
    except subprocess.TimeoutExpired:
        return 1, [], "Command timed out"
    except Exception as e:
        return 1, [], str(e)

def start_android_emulator(avd_name: str, background: bool = True) -> Tuple[int, str, str]:
    """Start Android emulator"""
    try:
        emulator_path = get_emulator_path()
        if not emulator_path:
            return 1, "", "Android emulator not found. Please install Android SDK."
        
        cmd = [emulator_path, "-avd", avd_name]
        
        if background:
            # Start in background
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return 0, f"Starting emulator {avd_name} in background (PID: {process.pid})", ""
        else:
            # Start in foreground (blocking)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def list_android_devices() -> Tuple[int, List[Dict[str, str]], str]:
    """List connected Android devices (via ADB)"""
    try:
        adb_path = get_adb_path()
        if not adb_path:
            return 1, [], "ADB not found. Please install Android SDK."
        
        result = subprocess.run(
            [adb_path, "devices", "-l"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return 1, [], result.stderr or "Failed to list devices"
        
        devices = []
        for line in result.stdout.strip().split('\n')[1:]:  # Skip header
            if line.strip() and 'List of devices' not in line:
                parts = line.split()
                if len(parts) >= 2:
                    devices.append({
                        "device_id": parts[0],
                        "status": parts[1],
                        "details": " ".join(parts[2:]) if len(parts) > 2 else ""
                    })
        
        return 0, devices, ""
    except subprocess.TimeoutExpired:
        return 1, [], "Command timed out"
    except Exception as e:
        return 1, [], str(e)

def run_android_studio_command(command: str, args: List[str] = None) -> Tuple[int, str, str]:
    """Run Android Studio command-line tool"""
    try:
        studio_bin = get_android_studio_bin()
        if not studio_bin and not shutil.which("studio"):
            return 1, "", "Android Studio not found. Please install Android Studio."
        
        cmd = [studio_bin or "studio"] + [command]
        if args:
            cmd.extend(args)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except Exception as e:
        return 1, "", str(e)

def open_android_sdk_manager() -> Tuple[int, str, str]:
    """Open Android SDK Manager"""
    try:
        android_home = get_android_home()
        if not android_home:
            return 1, "", "Android SDK not found. Please set ANDROID_HOME or install Android SDK."
        
        # Try to open SDK Manager via Android Studio
        sdk_manager_path = os.path.join(android_home, "tools", "bin", "sdkmanager")
        if not os.path.exists(sdk_manager_path):
            sdk_manager_path = os.path.join(android_home, "cmdline-tools", "latest", "bin", "sdkmanager")
        
        if os.path.exists(sdk_manager_path):
            # Open in terminal or return path
            if platform.system() == "Darwin":
                # Try to open Android Studio's SDK Manager
                studio_bin = get_android_studio_bin()
                if studio_bin:
                    return 0, "SDK Manager available. Open Android Studio > SDK Manager to use GUI.", ""
            return 0, f"SDK Manager at: {sdk_manager_path}. Run with: {sdk_manager_path} --list", ""
        
        return 1, "", "SDK Manager not found"
    except Exception as e:
        return 1, "", str(e)

def get_android_studio_info() -> Dict[str, Any]:
    """Get Android Studio and SDK information"""
    info = {
        "android_studio_found": False,
        "android_studio_path": None,
        "android_sdk_found": False,
        "android_sdk_path": None,
        "adb_found": False,
        "adb_path": None,
        "emulator_found": False,
        "emulator_path": None,
        "platform_tools_path": None,
        "tools_path": None,
    }
    
    studio_path = find_android_studio()
    if studio_path:
        info["android_studio_found"] = True
        info["android_studio_path"] = studio_path
    
    android_home = get_android_home()
    if android_home:
        info["android_sdk_found"] = True
        info["android_sdk_path"] = android_home
        
        platform_tools = os.path.join(android_home, "platform-tools")
        if os.path.exists(platform_tools):
            info["platform_tools_path"] = platform_tools
        
        tools = os.path.join(android_home, "tools")
        if os.path.exists(tools):
            info["tools_path"] = tools
    
    adb_path = get_adb_path()
    if adb_path:
        info["adb_found"] = True
        info["adb_path"] = adb_path
    
    emulator_path = get_emulator_path()
    if emulator_path:
        info["emulator_found"] = True
        info["emulator_path"] = emulator_path
    
    return info
