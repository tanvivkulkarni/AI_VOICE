import os
from openai import OpenAI
from dotenv import load_dotenv
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
    You are an intent classification system for a health assistant.

    Your task is to classify the user's message into ONE of the following intents.

    INTENTS:
    Greeting - User says hello or starts conversation.
    Goodbye - User ends the conversation.
    collect_calories_consumed - User tells how many calories they ate today.
    make_diet_plan - User asks for a diet plan or meal suggestions.
    colect_number_of_steps_taken - User tells how many steps they walked.
    collect_distance_covered - User tells the distance they walked or ran.
    collect_aimed_calories_burn - User tells how many calories they want to burn.
    collect_aim_calorie_to_consume - User tells their target calories to consume.
    Requesting Information - User asks health or fitness related questions.
    Other - Any message that does not match the above.

    RULES:
    - Return ONLY the intent name.
    - Do NOT explain anything.
    - Do NOT return a sentence.
    - Return EXACTLY one label from the list.

    EXAMPLES:

    User: Hello
    Intent: Greeting

    User: Hi there
    Intent: Greeting

    User: Bye
    Intent: Goodbye

    User: I ate 2000 calories today
    Intent: collect_calories_consumed

    User: I walked 8000 steps today
    Intent: colect_number_of_steps_taken

    User: I ran 5 kilometers today
    Intent: collect_distance_covered

    User: I want to burn 500 calories daily
    Intent: collect_aimed_calories_burn

    User: My daily calorie target is 1800
    Intent: collect_aim_calorie_to_consume

    User: Can you make a diet plan for weight loss?
    Intent: make_diet_plan

    User: How many calories should I eat to lose weight?
    Intent: Requesting Information


    Now classify the following user input.

    User: "{text}"

    Intent:
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
                You are a health assistant chatbot.

                Your job is to respond based on the health category provided.

                Category: {intent}
                User input: {user_text}

                Rules:
                - Give short, clear responses.
                - Be helpful and supportive.
                - If the category is unknown, politely ask the user to clarify.
                - Do not provide medical diagnosis.
                - Focus only on general wellness advice.

                Categories you may receive:

                1. calories_consumed
                User has provided calories they consumed today.
                Respond by acknowledging it and giving a simple health suggestion.

                Example:
                "Thanks for sharing. Based on your calorie intake, make sure your meals include balanced nutrients like protein, fiber, and healthy fats."

                2. diet_plan
                User wants a diet plan.
                Provide a simple daily diet outline (breakfast, lunch, dinner, snacks).

                3. steps_taken
                User provided number of steps.
                Encourage physical activity and mention general daily step goals.

                Example:
                "Great job! Staying active with regular walking helps improve heart health."

                4. distance_covered
                User shared walking/running distance.
                Encourage consistency and hydration.

                5. aimed_calories_burn
                User shared a calorie burn goal.
                Give tips like cardio, strength training, or walking.

                6. aim_calorie_to_consume
                User shared their calorie intake target.
                Encourage balanced meals and proper nutrition.

                Keep responses under 1 sentences.
            """
    response = client.chat.completions.create(
        model="meta-llama/Llama-3.1-8B-Instruct",
        messages=[
            {"role":"system", "content":prompt}, {"role":"user", "content":user_text}
        ],
        )
    return response.choices[0].message.content.strip()