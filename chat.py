import uuid

import httpx
import streamlit as st


def main():
    st.set_page_config(page_title="Health Checker Chat", page_icon="💬")
    st.title("Health Checker Chatbot")
    st.write("Interact with the same health assistant that powers your FastAPI app.")

    # Ensure we have a stable session_id for backend state
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"web-{uuid.uuid4()}"

    # Initialise chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display previous messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    user_input = st.chat_input("Type your message here...")
    if user_input:
        # Show user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Call the FastAPI backend so answers come from the running server
        try:
            resp = httpx.post(
                "http://127.0.0.1:8000/chat",
                json={
                    "text": user_input,
                    "session_id": st.session_state.session_id,
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
            bot_response = data.get("reply", "Sorry, I could not understand the response from the server.")
        except Exception as e:
            bot_response = f"Sorry, there was an error talking to the server: {e}"

        # Show assistant response
        with st.chat_message("assistant"):
            st.markdown(bot_response)

        st.session_state.messages.append(
            {"role": "assistant", "content": bot_response}
        )


if __name__ == "__main__":
    main()

