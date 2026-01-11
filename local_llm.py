"""
Local LLM integration (Ollama support)
Provides fallback to local LLM when API is unavailable or when explicitly enabled
"""
import httpx
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

OLLAMA_API_BASE = "http://localhost:11434"
OLLAMA_DEFAULT_MODEL = "llama3.2"

def check_ollama_available() -> bool:
    """Check if Ollama is running and accessible
    
    Returns:
        True if Ollama is available, False otherwise
    """
    try:
        response = httpx.get(f"{OLLAMA_API_BASE}/api/tags", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False

def call_ollama_api(
    messages: List[Dict[str, str]], 
    model: str = OLLAMA_DEFAULT_MODEL,
    temperature: float = 0.1,
    max_tokens: int = 2048
) -> Optional[str]:
    """Call local Ollama API
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model name (default: llama3.2)
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        
    Returns:
        Response text if successful, None otherwise
    """
    if not check_ollama_available():
        logger.debug("Ollama not available")
        return None
    
    # Convert messages to Ollama prompt format
    # Ollama expects: {"model": "...", "prompt": "...", "stream": false}
    prompt_parts = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            prompt_parts.append(f"User: {content}")
        elif role == "assistant":
            prompt_parts.append(f"Assistant: {content}")
        elif role == "system":
            prompt_parts.append(f"System: {content}")
    
    prompt = "\n".join(prompt_parts) + "\nAssistant:"
    
    try:
        response = httpx.post(
            f"{OLLAMA_API_BASE}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            },
            timeout=60.0
        )
        response.raise_for_status()
        result = response.json()
        return result.get("response", "")
    except Exception as e:
        logger.error(f"Ollama API error: {e}")
        return None

def get_ollama_models() -> List[str]:
    """Get list of available Ollama models
    
    Returns:
        List of model names
    """
    try:
        response = httpx.get(f"{OLLAMA_API_BASE}/api/tags", timeout=2.0)
        response.raise_for_status()
        data = response.json()
        models = [model.get("name", "") for model in data.get("models", [])]
        return models
    except Exception:
        return []