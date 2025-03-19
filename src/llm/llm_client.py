from openai import OpenAI

# DeepSeek API密钥
DEEPSEEK_API_KEY = "sk-c2aaa8cf6fe543d7abc92f1ddc3338ab"  

def call_deepseek_api(prompt: str) -> str:
    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com"
    )

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a Python code generator. Given the official documentation of a POSIX Shell and a specific shell (e.g., Bash, Fish, Zsh), generate a Python Transformer that converts a POSIX Shell script to the target shell script."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=3000,
        temperature=0.2,
        stream=False
    )

    if response:
        return response.choices[0].message.content.strip()
    else:
        raise Exception(f"Error: {response.status_code}, {response.text}")