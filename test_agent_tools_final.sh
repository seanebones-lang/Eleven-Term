#!/bin/bash
# Final comprehensive test of all agent tools
# Tests that agents can actually use all tools

set -e

echo "==========================================="
echo "FINAL COMPREHENSIVE AGENT TOOL TEST"
echo "==========================================="
echo ""

cd "$(dirname "$0")"

# Test 1: Python dependencies
echo "1. Testing Python dependencies..."
python3 << 'PYEOF'
import sys
packages = ["httpx", "termcolor"]
missing = []
for pkg in packages:
    try:
        __import__(pkg)
        print(f"   ✅ {pkg}")
    except ImportError:
        print(f"   ❌ {pkg} - MISSING")
        missing.append(pkg)

if missing:
    print(f"\n   Installing missing packages: {', '.join(missing)}")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "--user"] + missing, check=True)
    print("   ✅ Packages installed")
PYEOF

echo ""

# Test 2: Run comprehensive Python test
echo "2. Running comprehensive tool test..."
python3 test_all_tools_comprehensive.py

echo ""

# Test 3: Run integration test
echo "3. Running tool integration test..."
python3 test_tools_integration.py

echo ""

# Test 4: Run agent tool test
echo "4. Running agent tool access test..."
python3 << 'PYEOF'
import sys
import subprocess
sys.path.insert(0, '.')

try:
    from grok_agent import TOOLS, tool_bash
    
    print(f"   ✅ {len(TOOLS)} tools registered")
    
    # Test one tool execution
    result = tool_bash({"command": "echo 'Agent tools working'"})
    if result[0] == 0:
        print("   ✅ Tool execution: Working")
    else:
        print(f"   ❌ Tool execution: Failed (code: {result[0]})")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYEOF

echo ""
echo "==========================================="
echo "✅ ALL TESTS COMPLETE"
echo "==========================================="
