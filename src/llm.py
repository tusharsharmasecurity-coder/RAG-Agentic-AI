"""
NVIDIA NIM LLM Service
----------------------

Central LLM interface for the Delhivery Agentic AI project.

Provider:
    NVIDIA NIM

Model:
    Configured through NVIDIA_MODEL in .env

This module exposes:

    ask_llm(user_message, conversation_history)

All agents should call this function instead of
creating their own LLM client.
"""

import os

from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA


# ---------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------

load_dotenv()


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_MODEL = os.getenv(
    "NVIDIA_MODEL",
    "openai/gpt-oss-20b",
)


# ---------------------------------------------------------
# Validate configuration
# ---------------------------------------------------------

if not NVIDIA_API_KEY:
    raise RuntimeError(
        "NVIDIA_API_KEY is missing. "
        "Please add NVIDIA_API_KEY to your .env file."
    )


# ---------------------------------------------------------
# Create LLM
# ---------------------------------------------------------

def _create_llm():
    """
    Create a fresh NVIDIA Chat model.

    A function is used instead of creating the model at
    module import time so that importing this module does
    not unnecessarily initialize the API client.
    """

    return ChatNVIDIA(
        model=NVIDIA_MODEL,
        api_key=NVIDIA_API_KEY,
        temperature=0.2,
        max_tokens=512,
    )


# ---------------------------------------------------------
# Main LLM function
# ---------------------------------------------------------

def ask_llm(
    user_message: str,
    conversation_history: list,
) -> str:
    """
    Send a user message and conversation history
    to the NVIDIA hosted NIM model.

    Args:
        user_message:
            Latest user question.

        conversation_history:
            Previous messages in LangChain/OpenAI style:

            [
                {
                    "role": "user",
                    "content": "Hello"
                },
                {
                    "role": "assistant",
                    "content": "Hi!"
                }
            ]

    Returns:
        Plain-text model response.
    """

    if not user_message:
        return "Please enter a question."

    user_message = str(user_message).strip()

    if not user_message:
        return "Please enter a question."

    if conversation_history is None:
        conversation_history = []

    # -----------------------------------------------------
    # System instruction
    # -----------------------------------------------------

    system_message = {
        "role": "system",
        "content": (
            "You are Delhivery AI, a helpful logistics assistant. "
            "Answer clearly and accurately. "
            "Do not invent database values, shipment counts, "
            "or company-specific information that has not been "
            "provided to you."
        ),
    }

    # -----------------------------------------------------
    # Build message list
    # -----------------------------------------------------

    messages = [system_message]

    # Add previous conversation
    messages.extend(conversation_history)

    # Add current user message
    messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    # -----------------------------------------------------
    # Call NVIDIA NIM
    # -----------------------------------------------------

    try:

        llm = _create_llm()

        # IMPORTANT:
        # Modern LangChain uses invoke(), not llm(messages)
        response = llm.invoke(messages)

        # ChatNVIDIA returns an AIMessage.
        content = getattr(response, "content", None)

        if content is None:
            return "⚠️ No response from LLM."

        content = str(content).strip()

        if not content:
            return "⚠️ No response from LLM."

        return content

    except Exception as exc:

        print(
            f"[LLM ERROR] {type(exc).__name__}: {exc}",
            flush=True,
        )

        raise