class LLMClient:
    def __init__(self, config: dict):
        self.provider_name = config["llm"]["provider"]
        self.model = config["llm"]["model"]
        self.max_tokens = config["llm"]["max_tokens"]
        self.temperature = config["llm"]["temperature"]
        self.rate_limit = config["llm"]["rate_limit_per_minute"]
        
        self.provider = self._initialize_provider()

    def _initialize_provider(self):
        from .factory import create_provider
        return create_provider(self.provider_name, self.model, self.max_tokens, self.temperature)

    def generate_response(self, prompt: str):
        return self.provider.generate_response(prompt)

    def set_rate_limit(self, limit: int):
        self.rate_limit = limit
        self.provider.set_rate_limit(limit)