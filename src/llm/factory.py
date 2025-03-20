from typing import Dict
from .providers.base import BaseProvider
from .providers.openai import OpenAIClient

def create_llm_provider(config: Dict) -> BaseProvider:
    provider_name = config["llm"]["provider"]
    
    if provider_name == "openai":
        return OpenAIClient(config)
    elif provider_name == "deepseek":
        raise ValueError(f"Unknown LLM provider: {provider_name}")
    else:
        raise ValueError(f"Unknown LLM provider: {provider_name}")