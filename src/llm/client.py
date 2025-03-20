from src.llm.factory import create_llm_provider
from src.llm.providers.base import BaseProvider
from typing import Dict, Any

class LLMClient:
    def __init__(self, config: Dict[str, Any]):
        self.provider = self._initialize_provider(config)

    def _initialize_provider(self, config: Dict[str, Any]) -> BaseProvider:
        return create_llm_provider(config)

    def generate_response(self, prompt: str):
        response = self.provider.generate_response(prompt)
        content = self.provider.validate_response(response)
        return content
    
    def refine_code(self, prompt: str):
        response = self.provider.refine_code(prompt)
        content = self.provider.validate_response(response)
        return content

    def clear_history(self):
        self.provider.clear_conversation_history() 