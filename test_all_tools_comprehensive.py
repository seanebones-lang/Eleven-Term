#!/usr/bin/env python3
"""
Comprehensive tool testing for NextEleven Terminal Agent
Tests all tools to ensure they are accessible and functional
"""

import subprocess
import shutil
import sys
import os
import json
from typing import Dict, List, Tuple, Optional
from pathlib import Path

class ToolTester:
    def __init__(self):
        self.results = {
            "passed": [],
            "failed": [],
            "warnings": [],
            "fixed": []
        }
        self.test_dir = Path("/tmp/grok_tool_test")
        self.test_dir.mkdir(exist_ok=True)
    
    def test_tool_presence(self, tool: str, category: str) -> bool:
        """Test if tool is present in PATH"""
        path = shutil.which(tool)
        if path:
            self.results["passed"].append((category, tool, f"Found at {path}"))
            return True
        else:
            self.results["failed"].append((category, tool, "Not found in PATH"))
            return False
    
    def test_tool_execution(self, tool: str, args: List[str], category: str, expected_code: int = 0) -> bool:
        """Test if tool can execute"""
        try:
            result = subprocess.run(
                [tool] + args,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == expected_code or expected_code == -1:
                self.results["passed"].append((category, tool, f"Executed successfully"))
                return True
            else:
                self.results["warnings"].append((category, tool, f"Exit code {result.returncode}, expected {expected_code}"))
                return True  # Still counts as available
        except subprocess.TimeoutExpired:
            self.results["failed"].append((category, tool, "Execution timed out"))
            return False
        except FileNotFoundError:
            self.results["failed"].append((category, tool, "Tool not found"))
            return False
        except Exception as e:
            self.results["failed"].append((category, tool, f"Error: {str(e)}"))
            return False
    
    def test_python_package(self, package: str, category: str) -> bool:
        """Test if Python package is importable"""
        try:
            __import__(package)
            self.results["passed"].append((category, package, "Importable"))
            return True
        except ImportError:
            self.results["failed"].append((category, package, "Cannot import"))
            return False
        except Exception as e:
            self.results["warnings"].append((category, package, f"Import warning: {str(e)}"))
            return True
    
    def install_missing_tool(self, tool: str, formula: Optional[str] = None) -> bool:
        """Attempt to install missing tool via Homebrew"""
        if not shutil.which("brew"):
            return False
        
        formula = formula or tool
        try:
            result = subprocess.run(
                ["brew", "install", formula],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            if result.returncode == 0:
                if shutil.which(tool):
                    self.results["fixed"].append((tool, f"Installed via brew install {formula}"))
                    return True
        except Exception:
            pass
        return False
    
    def test_essential_tools(self):
        """Test essential tools"""
        print("📦 Testing Essential Tools...")
        tools = [
            ("fzf", ["--version"], -1),  # Exit code may vary
            ("tree", ["--version"], -1),
            ("jq", ["--version"], -1),
            ("git", ["--version"], -1),
            ("python3", ["--version"], -1),
            ("pip3", ["--version"], -1),
            ("wget", ["--version"], -1),
        ]
        
        for tool, args, expected in tools:
            if not self.test_tool_presence(tool, "Essential"):
                # Try to install
                if tool in ["fzf", "tree", "jq", "wget"]:
                    self.install_missing_tool(tool)
                    if shutil.which(tool):
                        self.test_tool_execution(tool, args, "Essential", expected)
            else:
                self.test_tool_execution(tool, args, "Essential", expected)
        print()
    
    def test_enhanced_tools(self):
        """Test enhanced productivity tools"""
        print("⚡ Testing Enhanced Tools...")
        tools = [
            ("rg", ["--version"], -1),
            ("bat", ["--version"], -1),
            ("fd", ["--version"], -1),
            ("htop", ["--version"], -1),
        ]
        
        for tool, args, expected in tools:
            if not self.test_tool_presence(tool, "Enhanced"):
                # Try to install
                formula_map = {"rg": "ripgrep", "bat": "bat", "fd": "fd", "htop": "htop"}
                formula = formula_map.get(tool, tool)
                self.install_missing_tool(tool, formula)
                if shutil.which(tool):
                    self.test_tool_execution(tool, args, "Enhanced", expected)
            else:
                self.test_tool_execution(tool, args, "Enhanced", expected)
        print()
    
    def test_xcode_tools(self):
        """Test Xcode development tools"""
        print("📱 Testing Xcode Tools...")
        tools = [
            ("xcodebuild", ["-version"], -1),
            ("xcrun", ["--version"], -1),
            ("swift", ["--version"], -1),
            ("pod", ["--version"], -1),
        ]
        
        for tool, args, expected in tools:
            if self.test_tool_presence(tool, "Xcode"):
                self.test_tool_execution(tool, args, "Xcode", expected)
            elif tool == "pod":
                # Try to install CocoaPods
                self.install_missing_tool("pod", "cocoapods")
                if shutil.which(tool):
                    self.test_tool_execution(tool, args, "Xcode", expected)
        print()
    
    def test_android_tools(self):
        """Test Android development tools"""
        print("🤖 Testing Android Tools...")
        
        # Check ANDROID_HOME
        android_home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
        if android_home and os.path.exists(android_home):
            self.results["passed"].append(("Android", "ANDROID_HOME", f"Set to {android_home}"))
            
            # Test ADB
            adb_path = os.path.join(android_home, "platform-tools", "adb")
            if os.path.exists(adb_path):
                if self.test_tool_execution(adb_path, ["version"], "Android", -1):
                    self.results["passed"].append(("Android", "adb", f"Available at {adb_path}"))
            
            # Test emulator
            emulator_path = os.path.join(android_home, "emulator", "emulator")
            if os.path.exists(emulator_path):
                self.results["passed"].append(("Android", "emulator", f"Available at {emulator_path}"))
        else:
            self.results["warnings"].append(("Android", "ANDROID_HOME", "Not set (Android tools may not be accessible)"))
        
        # Also check if in PATH
        if shutil.which("adb"):
            self.test_tool_execution("adb", ["version"], "Android", -1)
        if shutil.which("emulator"):
            self.test_tool_execution("emulator", ["-version"], "Android", -1)
        print()
    
    def test_development_tools(self):
        """Test development tools"""
        print("🔧 Testing Development Tools...")
        tools = [
            ("gh", ["--version"], -1),
            ("git-lfs", ["version"], -1),
            ("node", ["--version"], -1),
            ("npm", ["--version"], -1),
            ("docker", ["--version"], -1),
        ]
        
        for tool, args, expected in tools:
            if self.test_tool_presence(tool, "Development"):
                self.test_tool_execution(tool, args, "Development", expected)
            elif tool in ["gh", "git-lfs", "node", "npm", "docker"]:
                # Try to install
                formula_map = {
                    "gh": "gh",
                    "git-lfs": "git-lfs",
                    "node": "node",
                    "docker": "docker"
                }
                formula = formula_map.get(tool, tool)
                if self.install_missing_tool(tool, formula):
                    self.test_tool_execution(tool, args, "Development", expected)
        print()
    
    def test_build_tools(self):
        """Test build tools"""
        print("🏗️  Testing Build Tools...")
        tools = [
            ("make", ["--version"], -1),
            ("cmake", ["--version"], -1),
        ]
        
        for tool, args, expected in tools:
            if self.test_tool_presence(tool, "Build"):
                self.test_tool_execution(tool, args, "Build", expected)
            elif tool == "cmake":
                self.install_missing_tool("cmake")
                if shutil.which(tool):
                    self.test_tool_execution(tool, args, "Build", expected)
        print()
    
    def test_python_packages(self):
        """Test Python packages"""
        print("🐍 Testing Python Packages...")
        packages = [
            "httpx",
            "termcolor",
            "pytest",
            "black",
            "flake8",
            "mypy",
            "isort",
            "bandit",
        ]
        
        for package in packages:
            if not self.test_python_package(package, "Python"):
                # Try to install
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", "--user", package],
                        capture_output=True,
                        timeout=60
                    )
                    if self.test_python_package(package, "Python"):
                        self.results["fixed"].append((package, "Installed via pip"))
                except Exception:
                    pass
        print()
    
    def test_system_tools(self):
        """Test system tools"""
        print("💻 Testing System Tools...")
        tools = [
            ("curl", ["--version"], -1),
            ("tar", ["--version"], -1),
            ("gzip", ["--version"], -1),
        ]
        
        for tool, args, expected in tools:
            if self.test_tool_presence(tool, "System"):
                self.test_tool_execution(tool, args, "System", expected)
        print()
    
    def test_grok_agent_tools(self):
        """Test that grok_agent.py can access tools"""
        print("🤖 Testing Grok Agent Tool Access...")
        
        try:
            # Try to import grok_agent
            sys.path.insert(0, str(Path.cwd()))
            import grok_agent
            
            # Check TOOLS registry
            if hasattr(grok_agent, 'TOOLS'):
                tool_count = len(grok_agent.TOOLS)
                self.results["passed"].append(("Grok Agent", "TOOLS registry", f"{tool_count} tools registered"))
                
                # Check for key tools
                expected_tools = [
                    "Bash", "View", "Edit", "Write", "LS", "Glob", "Grep",
                    "XcodeProjectInfo", "XcodeListFiles", "AndroidProjectInfo", "AndroidListFiles"
                ]
                for tool_name in expected_tools:
                    if tool_name in grok_agent.TOOLS:
                        self.results["passed"].append(("Grok Agent", f"Tool: {tool_name}", "Registered"))
                    else:
                        self.results["failed"].append(("Grok Agent", f"Tool: {tool_name}", "Not in TOOLS registry"))
            else:
                self.results["failed"].append(("Grok Agent", "TOOLS registry", "Not found"))
                
        except ImportError as e:
            self.results["failed"].append(("Grok Agent", "Import", f"Cannot import: {str(e)}"))
        except Exception as e:
            self.results["failed"].append(("Grok Agent", "Error", str(e)))
        print()
    
    def print_summary(self):
        """Print test summary"""
        print("=" * 70)
        print("COMPREHENSIVE TOOL TEST SUMMARY")
        print("=" * 70)
        print()
        
        total_passed = len(self.results["passed"])
        total_failed = len(self.results["failed"])
        total_warnings = len(self.results["warnings"])
        total_fixed = len(self.results["fixed"])
        
        print(f"✅ Passed: {total_passed}")
        print(f"❌ Failed: {total_failed}")
        print(f"⚠️  Warnings: {total_warnings}")
        print(f"🔧 Fixed: {total_fixed}")
        print()
        
        if self.results["failed"]:
            print("❌ FAILED TESTS:")
            for category, tool, reason in self.results["failed"]:
                print(f"  {category}: {tool} - {reason}")
            print()
        
        if self.results["warnings"]:
            print("⚠️  WARNINGS:")
            for category, tool, reason in self.results["warnings"]:
                print(f"  {category}: {tool} - {reason}")
            print()
        
        if self.results["fixed"]:
            print("🔧 FIXED:")
            for tool, action in self.results["fixed"]:
                print(f"  {tool} - {action}")
            print()
        
        print("=" * 70)
        success_rate = (total_passed / (total_passed + total_failed) * 100) if (total_passed + total_failed) > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        print("=" * 70)
        
        return total_failed == 0
    
    def run_all_tests(self):
        """Run all tests"""
        print("=" * 70)
        print("COMPREHENSIVE TOOL TESTING")
        print("=" * 70)
        print()
        
        self.test_essential_tools()
        self.test_enhanced_tools()
        self.test_xcode_tools()
        self.test_android_tools()
        self.test_development_tools()
        self.test_build_tools()
        self.test_python_packages()
        self.test_system_tools()
        self.test_grok_agent_tools()
        
        return self.print_summary()

if __name__ == "__main__":
    tester = ToolTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
