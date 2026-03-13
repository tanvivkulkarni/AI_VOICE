import os
from openai import OpenAI
from dotenv import load_dotenv
import os
from huggingface_hub import InferenceClient


load_dotenv()  # This loads the .env file

api_key = os.getenv("OPENAI_API_KEY")
# print(api_key)  # test

if not api_key:
    raise RuntimeError(
        "OPENAI_API_KEY environment variable not set. "
        "Please set it before running the application."
    )

# client = OpenAI(api_key=api_key)
client = InferenceClient(
    api_key=os.getenv("HUGGINGFACE_API_KEY")
)
async def detect_intent(text):
    print("Detecting intent...")
    prompt = f"""
                You are a helpful assistant that identifies user intent from their input.
                Given the user's input, classify it into one of the following intents:
                Greeting
                Goodbye
                Requesting Information
                Providing Information
                Other

                give the intent in the above format without any explanation. Only return the intent name.
                for example, if the user says "Hello, how are you?" the intent would be "Greeting".
                so return "Greeting" without quotes and without any explanation.
            """
    # response= client.chat.completions.create(
    #     model="gpt-4o-mini", 
    #     messages=[{"role":"system", "content":prompt}, {"role":"user", "content":text}]
    # )
    # return response.choices[0].message.content.strip()
 
    response = client.chat.completions.create(
    model="meta-llama/Llama-3.1-8B-Instruct",
    messages=[
        {"role":"system", "content":prompt}, {"role":"user", "content":text}
    ],
    max_tokens=100
    )
    return response.choices[0].message.content.strip()

async def generate_response(intent, user_text):
    print("Generating response...")
    prompt = f"""
                You are a helpful assistant that generates responses based on user input and {intent}.
                Given the user's input and the detected intent, generate an appropriate response.
                it should be not be more than 100 tokens, means answer should be short and concise.
            """
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.1-8B-Instruct",
        messages=[
            {"role":"system", "content":prompt}, {"role":"user", "content":user_text}
        ],
        max_tokens=100
        )
    return response.choices[0].message.content.strip()