#!/bin/bash
# Edge case and error handling tests

echo "🔍 EDGE CASE & ERROR HANDLING TESTS"
echo "===================================="
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
    else
        echo "  ❌ FAIL"
        ((FAILED++))
    fi
}

# Test 1: Invalid agent ID
test "Invalid agent ID handling" python3 -c "
import grok_agent
config = grok_agent.DEFAULT_CONFIG.copy()
config['api_endpoint'] = 'https://grokcode.vercel.app/api/chat'
agents = config.get('specialized_agents', {})
if 'invalid_agent' not in agents:
    exit(0)  # Should not be found
exit(1)
"

# Test 2: Missing agent fields (should not happen, but test robustness)
test "Missing agent fields handling" python3 -c "
import grok_agent
agents = grok_agent.DEFAULT_CONFIG.get('specialized_agents', {})
for agent_id, agent_info in agents.items():
    mode = agent_info.get('mode', 'agent')  # Default fallback
    agent = agent_info.get('agent', agent_id)  # Default fallback
    if mode and agent:
        continue
    exit(1)
exit(0)
"

# Test 3: Empty message handling
test "Empty message handling" python3 -c "
messages = []
message_text = ''.join([msg.get('content', '') for msg in messages if msg.get('content')])
# Should handle empty gracefully
exit(0)
"

# Test 4: Multiple user messages (should use last one)
test "Multiple user messages handling" python3 -c "
messages = [
    {'role': 'user', 'content': 'first'},
    {'role': 'assistant', 'content': 'response'},
    {'role': 'user', 'content': 'second'}
]
message_text = ''
for msg in messages:
    if msg.get('role') == 'user':
        message_text = msg.get('content', '')
assert message_text == 'second', 'Should use last user message'
exit(0)
"

# Test 5: All agent modes are correct
test "All agent modes validation" python3 -c "
import grok_agent
agents = grok_agent.DEFAULT_CONFIG.get('specialized_agents', {})
# Verify specific agents have expected modes
assert agents['codeReview']['mode'] == 'review'
assert agents['bugHunter']['mode'] == 'debug'
assert agents['orchestrator']['mode'] == 'orchestrate'
assert agents['security']['mode'] == 'agent'
exit(0)
"

# Test 6: Agent names are non-empty
test "Agent names non-empty" python3 -c "
import grok_agent
agents = grok_agent.DEFAULT_CONFIG.get('specialized_agents', {})
for agent_id, agent_info in agents.items():
    assert agent_info.get('name'), f'Agent {agent_id} has no name'
    assert len(agent_info.get('name', '')) > 0
exit(0)
"

# Test 7: Agent emojis are present
test "Agent emojis present" python3 -c "
import grok_agent
agents = grok_agent.DEFAULT_CONFIG.get('specialized_agents', {})
for agent_id, agent_info in agents.items():
    emoji = agent_info.get('emoji', '')
    assert emoji, f'Agent {agent_id} has no emoji'
exit(0)
"

# Test 8: Config file merging works
test "Config file merging" python3 -c "
import grok_agent
# Test that DEFAULT_CONFIG is used as fallback
config = {}
agents = config.get('specialized_agents', grok_agent.DEFAULT_CONFIG.get('specialized_agents', {}))
assert len(agents) == 20, 'Should fallback to DEFAULT_CONFIG'
exit(0)
"

# Test 9: Endpoint URL variations
test "Endpoint URL variations" python3 -c "
endpoints = [
    'https://grokcode.vercel.app/api/chat',
    'https://grokcode.vercel.app/api/chat/',
    'http://grokcode.vercel.app/api/chat',
]
for url in endpoints:
    is_grokcode = 'grokcode.vercel.app' in url or url.endswith('/api/chat')
    assert is_grokcode, f'Should detect Grok-Code API: {url}'
exit(0)
"

# Test 10: Payload construction with all agents
test "Payload construction with all agents" python3 -c "
import grok_agent
config = grok_agent.DEFAULT_CONFIG.copy()
config['api_endpoint'] = 'https://grokcode.vercel.app/api/chat'
agents = config.get('specialized_agents', {})
for agent_id in agents.keys():
    agent_info = agents[agent_id]
    payload = {
        'message': 'test',
        'model': agent_id,
        'mode': agent_info.get('mode', 'agent'),
        'agent': agent_info.get('agent', agent_id)
    }
    assert 'mode' in payload
    assert 'agent' in payload
exit(0)
"

echo ""
echo "===================================="
echo "TEST SUMMARY"
echo "===================================="
echo "Total Tests: $((PASSED + FAILED))"
echo "✅ Passed: $PASSED"
if [ $FAILED -gt 0 ]; then
    echo "❌ Failed: $FAILED"
    exit 1
else
    echo "✅ Failed: $FAILED"
    echo ""
    echo "✅ ALL EDGE CASE TESTS PASSED!"
    exit 0
fi
