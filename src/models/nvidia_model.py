import os
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA

load_dotenv()

def nvidia_llm(model="nvidia/nemotron-3-ultra-550b-a55b"):
    return ChatNVIDIA(
        model=model,
        api_key=os.getenv("NVIDIA_API_KEY"),
        temperature=0,
    )