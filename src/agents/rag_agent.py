from src.knowledge.retriever import KnowledgeRetriever
from src.models.router import ModelRouter
from src.logger import log


class RAGAgent:

    def __init__(self):
        self.retriever = KnowledgeRetriever()
        self.router = ModelRouter()
        log("RAG_AGENT", "Ready")

    def ask(self, question: str):

        log("RAG_AGENT", f"Question: {question}")

        docs = self.retriever.search(question)

        context = "\n\n".join(docs)

        if not context:
            return "I couldn't find this information in the SOP."

        prompt = f"""
You are Delhivery AI.

Answer ONLY from the provided context.

If the answer is not found, say:
"I couldn't find this information in the SOP."

Context:
{context}

Question:
{question}
"""

        response = self.router.rag().invoke(prompt)

        return response.content.strip()