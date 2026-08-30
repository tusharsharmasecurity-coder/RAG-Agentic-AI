from src.models.ollama_model import llm
from src.models.nvidia_model import nvidia_llm


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
        return self._get("planner", nvidia_llm)

    # -----------------------------
    # SQL
    # -----------------------------

    def sql(self):
        return self._get("sql", lambda: llm("deepseek-coder:6.7b"))

    # -----------------------------
    # RAG
    # -----------------------------

    def rag(self):
        return self._get("rag", lambda: llm("llama3:8b"))

    # -----------------------------
    # Dashboard
    # -----------------------------

    def dashboard(self):
        return self._get("dashboard", lambda: llm("qwen3:8b"))

    # -----------------------------
    # Chat
    # -----------------------------

    def chat(self):
        return self._get("chat", lambda: llm("qwen3:8b"))

    # -----------------------------
    # Future Supervisor
    # -----------------------------

    def supervisor(self):
        return self._get("supervisor", nvidia_llm)

    # -----------------------------
    # Future Evaluator
    # -----------------------------

    def evaluator(self):
        return self._get("evaluator", nvidia_llm)
