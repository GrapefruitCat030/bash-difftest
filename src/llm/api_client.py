"""
LLM API Client module for interacting with language model providers
"""

import logging
import time
from typing import Dict, Any, Optional, List, Union
import os

import requests

logger = logging.getLogger(__name__)

class LLMClient:
    """Client for interacting with Language Model APIs"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the LLM client
        
        Args:
            config: Configuration dictionary containing API details
                - provider: Name of the provider (openai, anthropic, etc.)
                - api_key: API key for authentication
                - model: Model name to use
                - max_tokens: Maximum tokens for responses
                - temperature: Sampling temperature
        """
        self.provider = config["provider"]
        self.api_key = config.get("api_key") or os.environ.get(f"{self.provider.upper()}_API_KEY")
        self.model = config["model"]
        self.max_tokens = config.get("max_tokens", 4096)
        self.temperature = config.get("temperature", 0.7)
        
        # Keep track of token usage
        self.token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
        
        # Rate limiting parameters
        self.request_count = 0
        self.last_request_time = 0
        self.rate_limit_per_minute = config.get("rate_limit_per_minute", 10)
        
        logger.info(f"Initialized LLM client for provider: {self.provider}, model: {self.model}")

    def generate_code(self, prompt: str, context: Optional[Dict] = None) -> str:
        """
        Generate code using the configured LLM
        
        Args:
            prompt: The prompt to send to the LLM
            context: Additional context to include with the prompt
            
        Returns:
            Generated code as a string
        """
        # Rate limiting
        self._apply_rate_limiting()
        
        try:
            if self.provider == "openai":
                return self._call_openai_api(prompt, context)
            elif self.provider == "anthropic":
                return self._call_anthropic_api(prompt, context)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        except Exception as e:
            logger.error(f"Error generating code: {str(e)}")
            raise

    def refine_code(self, prompt: str, code: str, feedback: str) -> str:
        """
        Refine existing code based on feedback
        
        Args:
            prompt: The original prompt
            code: The code to refine
            feedback: Feedback about what needs to be fixed
            
        Returns:
            Refined code as a string
        """
        refinement_prompt = f"""
Original task:
{prompt}

Previous code attempt:
```python
{code}
```

Feedback that needs to be addressed: {feedback}

Please provide an improved version of the code that addresses the feedback: 
""" 
        return self.generate_code(refinement_prompt)
    
    def get_token_usage(self) -> Dict[str, int]:
        """Get the current token usage statistics"""
        return self.token_usage.copy()

    def _apply_rate_limiting(self):
        """Apply rate limiting to API calls"""
        current_time = time.time()
        if self.request_count >= self.rate_limit_per_minute:
            elapsed = current_time - self.last_request_time
            if elapsed < 60:  # Less than a minute has passed
                sleep_time = 60 - elapsed + 1  # +1 for safety
                logger.info(f"Rate limit reached. Sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                self.request_count = 0
                self.last_request_time = time.time()
        
        if current_time - self.last_request_time >= 60:
            # If more than a minute has passed, reset the counter
            self.request_count = 0
            self.last_request_time = current_time
            
        self.request_count += 1

    def _call_openai_api(self, prompt: str, context: Optional[Dict] = None) -> str:
        """Call OpenAI API"""
        import openai
        
        if context is None:
            context = {}
            
        # Set up the client with API key
        client = openai.Client(api_key=self.api_key)
        
        # Construct system message based on context
        system_message = context.get("system_message", "You are an expert shell script converter. Your task is to convert bash scripts to POSIX-compliant shell scripts while preserving functionality.")
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
        
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        
        # Update token usage
        self.token_usage["prompt_tokens"] += response.usage.prompt_tokens
        self.token_usage["completion_tokens"] += response.usage.completion_tokens
        self.token_usage["total_tokens"] += response.usage.total_tokens
        
        generated_text = response.choices[0].message.content
        return self._extract_code(generated_text)

    def _call_anthropic_api(self, prompt: str, context: Optional[Dict] = None) -> str:
        """Call Anthropic Claude API"""
        # Implementation for Anthropic's API
        # Similar to OpenAI implementation
        pass
        
    def _extract_code(self, text: str) -> str:
        """Extract code blocks from generated text"""
        import re
        
        # Look for Python code blocks with ```python ... ``` format
        code_blocks = re.findall(r'```(?:python)?\s*\n(.*?)\n```', text, re.DOTALL)
        
        if code_blocks:
            # Return the first code block found
            return code_blocks[0].strip()
        else:
            # If no code block found, return the entire text
            # after removing any markdown-style code annotations
            return text.replace('```python', '').replace('```', '').strip()
