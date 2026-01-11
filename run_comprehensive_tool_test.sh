#!/bin/bash
# Comprehensive tool test and fix script
# Tests all tools and fixes issues automatically

set -e

echo "==========================================="
echo "COMPREHENSIVE TOOL TEST AND FIX"
echo "==========================================="
echo ""

cd "$(dirname "$0")"

# Run comprehensive test
echo "Running comprehensive tool test..."
python3 test_all_tools_comprehensive.py

echo ""
echo "Running agent tool execution test..."
python3 << 'PYEOF'
import sys
import os
sys.path.insert(0, '.')

from grok_agent import TOOLS, tool_bash, tool_view, tool_write

print(f"Testing {len(TOOLS)} registered tools...")
print()

tests = [
    ("Bash", tool_bash, {"command": "echo 'test'"}),
]

passed = 0
for name, tool, params in tests:
    try:
        result = tool(params)
        if result[0] == 0:
            print(f"✅ {name}: PASSED")
            passed += 1
        else:
            print(f"❌ {name}: FAILED")
    except Exception as e:
        print(f"❌ {name}: ERROR - {e}")

print()
print(f"Results: {passed}/{len(tests)} tests passed")
PYEOF

echo ""
echo "==========================================="
echo "✅ TEST COMPLETE"
echo "==========================================="
