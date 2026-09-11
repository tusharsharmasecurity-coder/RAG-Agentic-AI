import os
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA

load_dotenv()

def nvidia_llm(model=None):
    model = model or os.getenv(
        "NVIDIA_MODEL",
        "meta/llama-3.1-70b-instruct",
    )

    return ChatNVIDIA(
        model=model,
        api_key=os.getenv("NVIDIA_API_KEY"),
        temperature=0,
    )