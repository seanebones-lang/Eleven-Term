"""
Agent chaining system
Allows chaining multiple specialized agents together for complex workflows
"""
import logging
from typing import List, Dict, Any, Optional, Callable

# Import from grok_agent (avoid circular imports by importing inside functions if needed)
try:
    from grok_agent import call_grok_api, get_api_key, load_config, DEFAULT_CONFIG
except ImportError:
    # Fallback - will be imported when needed
    call_grok_api = None  # type: ignore
    get_api_key = None  # type: ignore
    load_config = None  # type: ignore
    DEFAULT_CONFIG = {}  # type: ignore

logger = logging.getLogger(__name__)

class AgentChain:
    """Represents a chain of agents to execute sequentially"""
    
    def __init__(self, agents: List[str], config: Optional[Dict[str, Any]] = None):
        """Initialize agent chain
        
        Args:
            agents: List of agent names to chain (e.g., ["security", "performance", "testing"])
            config: Configuration dict
        """
        # Import here to avoid circular imports
        if load_config is None:
            from grok_agent import load_config
        
        self.agents = agents
        self.config = config or load_config()
        self.results: List[Dict[str, Any]] = []
    
    def execute(self, initial_message: str, api_key: Optional[str] = None) -> Dict[str, Any]:
        """Execute agent chain
        
        Args:
            initial_message: Initial user message
            api_key: API key (if None, will fetch from keychain)
            
        Returns:
            Dict with final_result and intermediate_results
        """
        # Import here to avoid circular imports
        if call_grok_api is None:
            from grok_agent import call_grok_api, get_api_key
        else:
            from grok_agent import get_api_key
        
        if api_key is None:
            api_key = get_api_key()
            if not api_key:
                raise ValueError("API key not found")
        
        current_message = initial_message
        intermediate_results = []
        
        for i, agent_name in enumerate(self.agents):
            logger.info(f"Executing agent {i+1}/{len(self.agents)}: {agent_name}")
            
            # Prepare messages for this agent
            messages = [{"role": "user", "content": current_message}]
            
            # Add context from previous agents if any
            if intermediate_results:
                context = f"\n\nPrevious agent results:\n{intermediate_results[-1].get('result', '')}"
                messages[0]["content"] += context
            
            # Call agent
            try:
                agent_config = self.config.copy()
                agent_config['model'] = agent_name
                agent_config['_explicit_agent_requested'] = True
                
                response = call_grok_api(
                    api_key=api_key,
                    messages=messages,
                    model=agent_name,
                    temperature=self.config.get("temperature", 0.1),
                    max_tokens=self.config.get("max_tokens", 2048),
                    config=agent_config
                )
                
                # Extract result
                if isinstance(response, dict) and "choices" in response:
                    result_text = response["choices"][0]["message"]["content"]
                elif isinstance(response, str):
                    result_text = response
                else:
                    result_text = str(response)
                
                intermediate_results.append({
                    "agent": agent_name,
                    "result": result_text,
                    "step": i + 1
                })
                
                # Use result as input for next agent
                current_message = result_text
                
            except Exception as e:
                logger.error(f"Error executing agent {agent_name}: {e}")
                intermediate_results.append({
                    "agent": agent_name,
                    "error": str(e),
                    "step": i + 1
                })
                break
        
        return {
            "final_result": current_message,
            "intermediate_results": intermediate_results,
            "success": len(intermediate_results) == len(self.agents)
        }

def chain_agents(agents: List[str], message: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Convenience function to chain agents
    
    Args:
        agents: List of agent names
        message: Initial message
        config: Optional configuration
        
    Returns:
        Chain execution result
    """
    # Import here to avoid circular imports
    if load_config is None:
        from grok_agent import load_config
    
    if config is None:
        config = load_config()
    
    chain = AgentChain(agents, config)
    return chain.execute(message)

# Predefined chains
SECURITY_REVIEW_CHAIN = ["security", "codeReview", "testing"]
PERFORMANCE_OPTIMIZATION_CHAIN = ["performance", "optimization", "testing"]
FULL_STACK_CHAIN = ["security", "performance", "testing", "documentation"]

def execute_security_review(message: str) -> Dict[str, Any]:
    """Execute security review chain
    
    Args:
        message: Initial message
        
    Returns:
        Chain result
    """
    return chain_agents(SECURITY_REVIEW_CHAIN, message)

def execute_performance_optimization(message: str) -> Dict[str, Any]:
    """Execute performance optimization chain
    
    Args:
        message: Initial message
        
    Returns:
        Chain result
    """
    return chain_agents(PERFORMANCE_OPTIMIZATION_CHAIN, message)

def execute_full_stack_review(message: str) -> Dict[str, Any]:
    """Execute full stack review chain
    
    Args:
        message: Initial message
        
    Returns:
        Chain result
    """
    return chain_agents(FULL_STACK_CHAIN, message)