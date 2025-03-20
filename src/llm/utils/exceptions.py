class LLMError(Exception):
    """Base class for exceptions in the LLM module."""
    pass

class ProviderNotFoundError(LLMError):
    """Exception raised when a specified LLM provider is not found."""
    def __init__(self, provider_name):
        self.provider_name = provider_name
        super().__init__(f"Provider '{provider_name}' not found.")

class InvalidConfigurationError(LLMError):
    """Exception raised for invalid configuration settings."""
    def __init__(self, message):
        super().__init__(message)

class RateLimitExceededError(LLMError):
    """Exception raised when the rate limit for API calls is exceeded."""
    def __init__(self, limit):
        self.limit = limit
        super().__init__(f"Rate limit of {limit} requests per minute exceeded.")