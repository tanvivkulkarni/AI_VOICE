import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()
client = InferenceClient(
    provider="fal-ai",
    api_key=os.environ["HUGGINGFACE_API_KEY"],
)

# audio is returned as bytes
audio = client.text_to_speech(
    "The answer to the universe is 42",
    model="hexgrad/Kokoro-82M",
)