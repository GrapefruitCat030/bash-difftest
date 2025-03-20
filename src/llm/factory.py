from typing import Dict, Any
from .providers.base import BaseProvider
from .providers.openai import OpenAIProvider

def create_llm_provider(config: Dict[str, Any]) -> BaseProvider:
    """
    Factory function to create an LLM provider based on the configuration. 
    """

    provider_name = config.get("provider")
    
    if provider_name == "openai":
        return OpenAIProvider(config)
    elif provider_name == "deepseek":
        raise ValueError(f"Unknown LLM provider: {provider_name}")
    else:
        raise ValueError(f"Unknown LLM provider: {provider_name}")