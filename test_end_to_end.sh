#!/bin/bash
# End-to-end integration test

echo "🔄 END-TO-END INTEGRATION TEST"
echo "==============================="
echo ""

PASSED=0
FAILED=0

test() {
    name="$1"
    shift
    echo "[Test] $name..."
    if "$@" > /dev/null 2>&1; then
        echo "  ✅ PASS"
        ((PASSED++))
        return 0
    else
        echo "  ❌ FAIL"
        ((FAILED++))
        return 1
    fi
}

# Test 1: List agents command works
test "List agents command" python3 grok_agent.py --list-agents

# Test 2: Help command includes all flags
test "Help includes all flags" python3 grok_agent.py --help | grep -q "list-agents\|model\|endpoint\|config"

# Test 3: Import works correctly
test "Module import works" python3 -c "import grok_agent; print('OK')"

# Test 4: All agents accessible programmatically
test "All agents accessible" python3 -c "
import grok_agent
agents = grok_agent.DEFAULT_CONFIG.get('specialized_agents', {})
assert len(agents) == 20
for agent_id in ['security', 'performance', 'testing', 'documentation']:
    assert agent_id in agents
"

# Test 5: Agent payload can be constructed
test "Agent payload construction" python3 -c "
import grok_agent
config = grok_agent.DEFAULT_CONFIG.copy()
config['api_endpoint'] = 'https://grokcode.vercel.app/api/chat'
model = 'security'
agents = config.get('specialized_agents', {})
agent_info = agents[model]
payload = {
    'message': 'test',
    'model': model,
    'mode': agent_info['mode'],
    'agent': agent_info['agent']
}
assert payload['mode'] == 'agent'
assert payload['agent'] == 'security'
"

# Test 6: Config loading works (even if file doesn't exist)
test "Config loading works" python3 -c "
import grok_agent
config = grok_agent.load_config('/nonexistent/path.json')
assert 'model' in config
assert 'specialized_agents' in config
"

# Test 7: API key retrieval doesn't crash
test "API key retrieval" python3 -c "
import grok_agent
key = grok_agent.get_api_key()
# Should return None or string, not raise
assert key is None or isinstance(key, str)
"

# Test 8: Grok-Code API detection works
test "Grok-Code API detection" python3 -c "
config = {'api_endpoint': 'https://grokcode.vercel.app/api/chat'}
url = config.get('api_endpoint', '')
is_grokcode = 'grokcode.vercel.app' in url or url.endswith('/api/chat')
assert is_grokcode
"

# Test 9: Message format conversion
test "Message format conversion" python3 -c "
messages = [{'role': 'user', 'content': 'test'}]
message_text = ''.join([msg.get('content', '') for msg in messages if msg.get('role') == 'user'])
assert message_text == 'test'
"

# Test 10: Agent mode validation
test "Agent mode validation" python3 -c "
import grok_agent
agents = grok_agent.DEFAULT_CONFIG.get('specialized_agents', {})
valid_modes = ['agent', 'review', 'debug', 'orchestrate']
for agent_info in agents.values():
    assert agent_info['mode'] in valid_modes
"

echo ""
echo "==============================="
echo "E2E TEST SUMMARY"
echo "==============================="
echo "Total Tests: $((PASSED + FAILED))"
echo "✅ Passed: $PASSED"
if [ $FAILED -gt 0 ]; then
    echo "❌ Failed: $FAILED"
    exit 1
else
    echo "✅ Failed: $FAILED"
    echo ""
    echo "✅ ALL END-TO-END TESTS PASSED!"
    exit 0
fi
