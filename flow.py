def handle_intent(intent, user_text, state):
    if state.step=="greeting":
        state.step="collect_reason"
        return "Hello! How can I assist you today?"
    elif state.step=="goodbye":
        return "Goodbye! Have a great day!"
    elif state.step=="collect_reason":
        state.date=user_text
        state.step="complete"
        return f"Thanks for providing your reason: {user_text}. I've noted it."
    else:
        return "I'm not sure how to respond to that."

