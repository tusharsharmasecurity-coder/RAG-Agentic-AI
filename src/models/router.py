from src.models.ollama_model import llm
from src.models.nvidia_model import nvidia_llm


class ModelRouter:

    def __init__(self):

        # -----------------------------
        # NVIDIA Models
        # -----------------------------

        self._planner = nvidia_llm()

        # These will be used later
        self._supervisor = nvidia_llm()
        self._evaluator = nvidia_llm()

        # -----------------------------
        # Ollama Models
        # -----------------------------

        self._sql = llm("deepseek-coder:6.7b")

        self._rag = llm("llama3:8b")

        self._dashboard = llm("qwen3:8b")

        self._chat = llm("qwen3:8b")

    # -----------------------------
    # Planner
    # -----------------------------

    def planner(self):
        return self._planner

    # -----------------------------
    # SQL
    # -----------------------------

    def sql(self):
        return self._sql

    # -----------------------------
    # RAG
    # -----------------------------

    def rag(self):
        return self._rag

    # -----------------------------
    # Dashboard
    # -----------------------------

    def dashboard(self):
        return self._dashboard

    # -----------------------------
    # Chat
    # -----------------------------

    def chat(self):
        return self._chat

    # -----------------------------
    # Future Supervisor
    # -----------------------------

    def supervisor(self):
        return self._supervisor

    # -----------------------------
    # Future Evaluator
    # -----------------------------

    def evaluator(self):
        return self._evaluator