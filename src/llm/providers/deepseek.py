import openai
from typing import Dict, Any
from .base import BaseProvider
from ..utils.retry import retry_with_exponential_backoff

class DeepseekProvider(BaseProvider):
    """
    Provider implementation for OpenAI's API using the official Python library.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.client = openai.OpenAI(api_key=self.api_key, base_url="https://api.deepseek.com")

    def generate_response(self, prompt: str):
        """
        Generate a response using OpenAI's Python library.
        """
        self.rate_limiter.wait()

        # deepseek Few-shot 可以提升模型的输出效果
        self.conversation_history.append({"role": "user", "content": prompt})

        def _generate_response():
            return self.client.chat.completions.create(
                model       = self.model,
                messages    = self.conversation_history,
                max_tokens  = self.max_tokens,
                temperature = self.temperature
            )
        response = retry_with_exponential_backoff(
            func = _generate_response,
            max_attempts=5,
            initial_delay=1,
            backoff_factor=2,
            max_delay=10,
            exceptions=(openai.error.OpenAIError,)
        )
        
        self.conversation_history.append(response["choices"][0]["message"])
        
        return response

    def validate_response(self, response: Dict[str, Any]) -> str:
        """
        Validate the OpenAI API response and extract the generated text.
        """
        if "error" in response:
            raise Exception(f"Error from OpenAI API: {response['error']}")
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            raise Exception("Invalid response format from OpenAI API")