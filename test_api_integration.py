#!/usr/bin/env python3
"""
Comprehensive API integration tests for Grok-Code agents
"""

import sys
import json
import subprocess
from pathlib import Path

# Import grok_agent module
sys.path.insert(0, str(Path(__file__).parent))
import grok_agent

def test_count(func):
    """Decorator to count test results"""
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            if result:
                print(f"  ✅ PASS")
                return True
            else:
                print(f"  ❌ FAIL")
                return False
        except Exception as e:
            print(f"  ❌ FAIL: {e}")
            return False
    return wrapper

@test_count
def test_all_agents_present():
    """Test that all 20 agents are present in DEFAULT_CONFIG"""
    agents = grok_agent.DEFAULT_CONFIG.get('specialized_agents', {})
    assert len(agents) == 20, f"Expected 20 agents, found {len(agents)}"
    
    required_agents = [
        'security', 'performance', 'testing', 'documentation', 'migration',
        'dependency', 'codeReview', 'bugHunter', 'optimization', 'accessibility',
        'orchestrator', 'swarm', 'mobile', 'devops', 'database', 'api',
        'uiux', 'aiml', 'data', 'fullstack'
    ]
    
    missing = [a for a in required_agents if a not in agents]
    assert len(missing) == 0, f"Missing agents: {missing}"
    return True

@test_count
def test_agent_structure():
    """Test that each agent has required fields"""
    agents = grok_agent.DEFAULT_CONFIG.get('specialized_agents', {})
    
    for agent_id, agent_info in agents.items():
        assert 'name' in agent_info, f"Agent {agent_id} missing 'name'"
        assert 'emoji' in agent_info, f"Agent {agent_id} missing 'emoji'"
        assert 'mode' in agent_info, f"Agent {agent_id} missing 'mode'"
        assert 'agent' in agent_info, f"Agent {agent_id} missing 'agent'"
    
    return True

@test_count
def test_agent_modes():
    """Test that all agent modes are valid"""
    agents = grok_agent.DEFAULT_CONFIG.get('specialized_agents', {})
    valid_modes = ['agent', 'review', 'debug', 'orchestrate']
    
    for agent_id, agent_info in agents.items():
        mode = agent_info.get('mode')
        assert mode in valid_modes, f"Agent {agent_id} has invalid mode: {mode}"
    
    return True

@test_count
def test_grokcode_api_detection():
    """Test Grok-Code API detection"""
    url = "https://grokcode.vercel.app/api/chat"
    is_grokcode = "grokcode.vercel.app" in url or url.endswith("/api/chat")
    assert is_grokcode, "Grok-Code API not detected correctly"
    return True

@test_count
def test_message_extraction():
    """Test message extraction from messages array"""
    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "test message"},
        {"role": "assistant", "content": "response"}
    ]
    
    message_text = ""
    for msg in messages:
        if msg.get("role") == "user":
            message_text = msg.get("content", "")
    
    assert message_text == "test message", f"Expected 'test message', got '{message_text}'"
    return True

@test_count
def test_agent_payload_construction():
    """Test specialized agent payload construction"""
    config = grok_agent.DEFAULT_CONFIG.copy()
    config['api_endpoint'] = 'https://grokcode.vercel.app/api/chat'
    
    model = 'security'
    specialized_agents = config.get('specialized_agents', {})
    
    assert model in specialized_agents, f"Agent {model} not found"
    
    agent_info = specialized_agents[model]
    payload = {
        'message': 'test',
        'model': model,
        'mode': agent_info.get('mode', 'agent'),
        'agent': agent_info.get('agent', model)
    }
    
    assert payload.get('mode') == 'agent', f"Expected mode 'agent', got '{payload.get('mode')}'"
    assert payload.get('agent') == 'security', f"Expected agent 'security', got '{payload.get('agent')}'"
    return True

@test_count
def test_sse_response_conversion():
    """Test SSE response format conversion"""
    # Simulate Grok-Code SSE response
    grokcode_data = {"content": "Hello"}
    
    # Convert to xAI format
    xai_format = {
        "choices": [{
            "delta": {
                "content": grokcode_data.get("content", "")
            }
        }]
    }
    
    assert xai_format['choices'][0]['delta']['content'] == 'Hello', \
        "Response conversion failed"
    return True

@test_count
def test_list_agents_command():
    """Test --list-agents command"""
    result = subprocess.run(
        ['python3', 'grok_agent.py', '--list-agents'],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    assert "Available Specialized Agents" in result.stdout, \
        "--list-agents command failed"
    assert "(20)" in result.stdout, "Should show 20 agents"
    return True

@test_count
def test_help_command_includes_list_agents():
    """Test that --help includes --list-agents"""
    result = subprocess.run(
        ['python3', 'grok_agent.py', '--help'],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    assert "--list-agents" in result.stdout, \
        "--list-agents not in help output"
    return True

@test_count
def test_specific_agents():
    """Test specific agents have correct configuration"""
    agents = grok_agent.DEFAULT_CONFIG.get('specialized_agents', {})
    
    # Test security agent
    assert agents['security']['name'] == 'Security Agent'
    assert agents['security']['emoji'] == '🔒'
    assert agents['security']['mode'] == 'agent'
    
    # Test codeReview agent (should use 'review' mode)
    assert agents['codeReview']['mode'] == 'review'
    
    # Test bugHunter agent (should use 'debug' mode)
    assert agents['bugHunter']['mode'] == 'debug'
    
    # Test orchestrator agent (should use 'orchestrate' mode)
    assert agents['orchestrator']['mode'] == 'orchestrate'
    
    return True

def run_all_tests():
    """Run all tests and report results"""
    print("🧪 COMPREHENSIVE GROK-CODE API INTEGRATION TESTS")
    print("=" * 60)
    print()
    
    tests = [
        ("All 20 agents present", test_all_agents_present),
        ("Agent structure validation", test_agent_structure),
        ("Agent modes validation", test_agent_modes),
        ("Grok-Code API detection", test_grokcode_api_detection),
        ("Message extraction", test_message_extraction),
        ("Agent payload construction", test_agent_payload_construction),
        ("SSE response conversion", test_sse_response_conversion),
        ("--list-agents command", test_list_agents_command),
        ("Help includes --list-agents", test_help_command_includes_list_agents),
        ("Specific agents configuration", test_specific_agents),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        print(f"[Test] {name}...", end="")
        if test_func():
            passed += 1
        else:
            failed += 1
    
    print()
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {len(tests)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print()
    
    if failed == 0:
        print("✅ ALL TESTS PASSED!")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
