from services.llm import generate_response

async def handle_intent(intent, user_text, state):
    if state.step=="greeting":
        return "Hello! How can I assist you today?"
    elif state.step=="goodbye":
        return "Goodbye! Have a great day!"        
    else:
        return "I'm not sure how to respond to that."

async def handle_health_information(intent, user_text, state):
    aimed_category=""

    def categories_of_health_information(user_text, intent):
        category=""
        if intent=="collect_calories_consumed":
            category="calories_consumed"
        elif intent=="make_diet_plan":
            category="diet_plan"
        elif intent=="colect_number_of_steps_taken":
            category="steps_taken"
        elif intent=="collect_distance_covered":
            category="distance_covered"
        elif intent=="collect_aimed_calories_burn":
            category="aimed_calories_burn"
        elif intent=="collect_aim_calorie_to_consume":
            category="aim_calorie_to_consume"
        else:
            category="Requesting Information"
        return category

    aimed_category=categories_of_health_information(user_text, intent)
    print(f"Aimed category: {aimed_category}")
    print(f"User text: {user_text}")
    bot_response = await generate_response(aimed_category, user_text)
    return bot_response