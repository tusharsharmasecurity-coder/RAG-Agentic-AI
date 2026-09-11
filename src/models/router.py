from src.models.ollama_model import llm
from src.models.nvidia_model import nvidia_llm
import os
from langchain_ollama import ChatOllama


class ModelRouter:

    def __init__(self):
        self._models = {}

    def _get(self, route, factory):
        if route not in self._models:
            self._models[route] = factory()
        return self._models[route]

    # -----------------------------
    # Planner
    # -----------------------------
    def planner(self):
        return self._get("planner", lambda: nvidia_llm())

    # -----------------------------
    # SQL (Use NVIDIA or deepseek-coder for clean SQL syntax)
    # -----------------------------
    def sql(self):
        return self._get("sql", lambda: nvidia_llm())

    # -----------------------------
    # RAG (Fast local 3B model ~14s)
    # -----------------------------

    def rag(self):
        # Force 127.0.0.1 fallback for native Windows execution
        base_url = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
        if not base_url:
            base_url = "http://host.docker.internal:11434"
        if "host.docker.internal" in base_url and not os.path.exists("/.dockerenv"):
            base_url = "http://127.0.0.1:11434"
        model_name = os.getenv("LLM_MODEL", "qwen3:8b")
        return ChatOllama(
            base_url=base_url,
            model=model_name,
            temperature=0,
            timeout=30.0,  # Prevent infinite network hanging
        )

    # -----------------------------
    # Dashboard (Fast local 3B model)
    # -----------------------------
    def dashboard(self):
        return self._get("dashboard", lambda: llm)

    # -----------------------------
    # Chat (Fast local 3B model ~3.6s)
    # -----------------------------
    def chat(self):
        return self._get("chat", lambda: llm)

    # -----------------------------
    # Supervisor / Evaluator
    # -----------------------------
    def supervisor(self):
        return self._get("supervisor", lambda: nvidia_llm())

    def evaluator(self):
        return self._get("evaluator", lambda: nvidia_llm())
