import streamlit as st

from src.llm_client import get_nvidia_client


def render_chat():
    st.subheader("🤖 Delhivery AI Assistant")

    # ---------------------------------------------------------
    # Initialize chat history
    # ---------------------------------------------------------
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {
                "role": "assistant",
                "content": (
                    "Hello! I am the Delhivery AI Assistant. "
                    "Ask me a question about your logistics data."
                ),
            }
        ]

    # ---------------------------------------------------------
    # Display previous messages
    # ---------------------------------------------------------
    for message in st.session_state.chat_messages:

        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # ---------------------------------------------------------
    # Chat input
    # ---------------------------------------------------------
    prompt = st.chat_input(
        "Ask something about your logistics data..."
    )

    if not prompt:
        return

    # ---------------------------------------------------------
    # Display user message
    # ---------------------------------------------------------
    st.session_state.chat_messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    # ---------------------------------------------------------
    # NVIDIA LLM request
    # ---------------------------------------------------------
    with st.chat_message("assistant"):

        try:
            with st.spinner("Thinking..."):

                client = get_nvidia_client()

                response = client.chat(
                    messages=st.session_state.chat_messages,
                    temperature=0.7,
                    max_tokens=1000,
                )

            st.markdown(response)

            st.session_state.chat_messages.append(
                {
                    "role": "assistant",
                    "content": response,
                }
            )

        except Exception as e:

            error_message = (
                "⚠️ I couldn't contact the NVIDIA model.\n\n"
                f"`{type(e).__name__}: {e}`"
            )

            st.error(error_message)