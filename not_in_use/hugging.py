from huggingface_hub import InferenceClient
from dotenv import load_dotenv
import os
from transformers import pipeline
from transformers import AutoTokenizer, AutoModelForCausalLM

load_dotenv()

client = InferenceClient(
    api_key=os.getenv("HUGGINGFACE_API_KEY")
)

response = client.chat.completions.create(
    model="meta-llama/Llama-3.1-8B-Instruct",
    messages=[
        {"role": "user", "content": "Corp is a difference between static method and class method"}
    ],
    max_tokens=100
)

print(response.choices[0].message.content)

