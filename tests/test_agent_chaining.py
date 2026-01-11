"""Tests for agent chaining"""
import pytest
from unittest.mock import Mock, patch
from agent_chaining import AgentChain, chain_agents

@pytest.fixture
def mock_api_key():
    return "test-api-key"

@pytest.fixture
def mock_config():
    return {
        "model": "grok-beta",
        "temperature": 0.1,
        "max_tokens": 2048
    }

@patch('agent_chaining.get_api_key')
@patch('agent_chaining.call_grok_api')
def test_agent_chain_execution(mock_call_api, mock_get_key, mock_api_key, mock_config):
    """Test agent chain execution"""
    mock_get_key.return_value = mock_api_key
    
    # Mock API responses
    mock_call_api.side_effect = [
        {"choices": [{"message": {"content": "Security review complete"}}]},
        {"choices": [{"message": {"content": "Performance review complete"}}]}
    ]
    
    chain = AgentChain(["security", "performance"], mock_config)
    result = chain.execute("Review my code", mock_api_key)
    
    assert result["success"]
    assert len(result["intermediate_results"]) == 2
    assert result["intermediate_results"][0]["agent"] == "security"
    assert result["intermediate_results"][1]["agent"] == "performance"

@patch('agent_chaining.get_api_key')
@patch('agent_chaining.call_grok_api')
def test_chain_agents_function(mock_call_api, mock_get_key, mock_api_key, mock_config):
    """Test chain_agents convenience function"""
    mock_get_key.return_value = mock_api_key
    mock_call_api.return_value = {"choices": [{"message": {"content": "Result"}}]}
    
    result = chain_agents(["security"], "Test message", mock_config)
    
    assert "final_result" in result
    assert "intermediate_results" in result