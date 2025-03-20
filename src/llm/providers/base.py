class BaseProvider:
    """
    Base class for all LLM providers. This class defines the common interface
    and properties that all LLM providers must implement.
    """

    def __init__(self, config: dict):
        """
        Initializes the BaseProvider with the given configuration.

        Args:
            config (dict): Configuration dictionary containing provider settings.
        """
        self.provider_name = config.get("provider")
        self.model = config.get("model")
        self.max_tokens = config.get("max_tokens")
        self.temperature = config.get("temperature")
        self.rate_limit_per_minute = config.get("rate_limit_per_minute")

    def generate_response(self, prompt: str) -> str:
        """
        Generate a response based on the provided prompt. This method must be
        implemented by subclasses.

        Args:
            prompt (str): The input prompt for the LLM.

        Returns:
            str: The generated response from the LLM.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def set_rate_limit(self, limit):
        """
        Set the rate limit for API calls.

        Args:
            limit (int): The new rate limit in requests per minute.
        """
        self.rate_limit_per_minute = limit

    def get_provider_info(self):
        """
        Get information about the provider.

        Returns:
            dict: A dictionary containing provider information.
        """
        return {
            "provider_name": self.provider_name,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "rate_limit_per_minute": self.rate_limit_per_minute,
        }