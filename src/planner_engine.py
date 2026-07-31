from src.planner import Planner
from src.memory.chat_memory import ChatMemory


class PlannerEngine:
    def __init__(self):
        self.planner = Planner()
        self.memory = ChatMemory()

    def create_plan(self, question):
        context = self.memory.get_context()
        intent = self.planner.plan(question, context)

        self.memory.add_user(question)

        if intent == "SQL":
            return {
                "intent": "SQL",
                "tools": ["sql"]
            }

        if intent == "RAG":
            return {
                "intent": "RAG",
                "tools": ["rag"]
            }

        if intent == "BOTH":
            return {
                "intent": "BOTH",
                "tools": ["sql", "rag"]
            }

        if intent == "DATAFRAME":
            return {
                "intent": "DATAFRAME",
                "tools": ["dataframe"]
            }

        return {
            "intent": "CHAT",
            "tools": []
        }