class OpenAIClient:
    def __init__(self, config):
        self.api_key = config["api_key"]
        self.model = config["model"]
        self.max_tokens = config["max_tokens"]
        self.temperature = config["temperature"]
        self.rate_limit_per_minute = config["rate_limit_per_minute"]
        self.base_url = "https://api.openai.com/v1/chat/completions"

    def generate_response(self, prompt):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        response = requests.post(self.base_url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()

    def set_rate_limit(self, limit):
        self.rate_limit_per_minute = limit

    def get_rate_limit(self):
        return self.rate_limit_per_minute

    def validate_response(self, response):
        if "error" in response:
            raise Exception(f"Error from OpenAI API: {response['error']['message']}")
        return response["choices"][0]["message"]["content"]