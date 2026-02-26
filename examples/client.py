from openai import OpenAI

# -------------
# 配置项
# -------------
BASE_URL = "http://localhost:8845/v1"
API_KEY = "EMPTY" 
MODEL_NAME = "qwen3-8b"


# Initialize the client pointing to the local vLLM server
client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
)

# Test completion
response = client.chat.completions.create(
    model=MODEL_NAME,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello! Who are you?"}
    ],
    max_tokens=100,
    temperature=0.7
)

print("Response from vLLM:")
print(response.choices[0].message.content)
