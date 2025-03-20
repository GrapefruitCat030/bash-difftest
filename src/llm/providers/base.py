from abc import ABC, abstractmethod
from typing import Dict, Any, List
from src.llm.utils import RateLimiter

class BaseProvider(ABC):
    """
    Base class for all LLM providers.
    """
    def __init__(self, config: Dict[str, Any]):
        self.provider_name = config.get("provider")
        self.model         = config.get("model")
        self.max_tokens    = config.get("max_tokens")
        self.temperature   = config.get("temperature")
        self.rate_limit_per_minute = config.get("rate_limit_per_minute", 60)
        self.rate_limiter = RateLimiter(self.rate_limit_per_minute)
        self.conversation_history: List[Dict[str, str]] = []

    @abstractmethod
    def generate_response(self, prompt: str) -> Any:
        """
        Generate a response based on the provided prompt. 
        
        Args:
            prompt (str): The input prompt for the LLM.
        Returns:
            Any: The generated response from the LLM.
        """
        pass

    @abstractmethod
    def validate_response(self, response: Any) -> str:
        """
        Validate and extract the content from the provider's response.
        
        Args:
            response (Any): The response object from the provider.
        Returns:
            str: The extracted and validated response content.
        """
        pass

    def set_rate_limit(self, limit: int) -> None:
        """
        Set the rate limit for API calls.
        Args:
            limit (int): The new rate limit in requests per minute.
        """
        self.rate_limit_per_minute = limit
        self.rate_limiter = RateLimiter(limit)

    def get_rate_limit(self) -> int:
        return self.rate_limit_per_minute

    def get_provider_info(self) -> Dict[str, Any]:
        return {
            "provider_name": self.provider_name,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "rate_limit_per_minute": self.rate_limit_per_minute,
        }

    def add_to_conversation(self, message:Dict[str, str]) -> None:
        self.conversation_history.append(message)

    def clear_conversation_history(self) -> None:
        self.conversation_history = []
