from streamlit import context

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

        docs = self.retriever.search(question, k=3)
        context = "\n\n".join(docs)

        

        if not context:
            return "I couldn't find this information in the SOP."

        prompt = f"""
You are a logistics SOP assistant.

Answer the question using ONLY the Context.

Rules:
- Do not use outside knowledge.
- Do not guess.
- Give a concise answer.
- Use 3-5 bullet points when appropriate.
- Include important TAT, evidence, POD, AWB, and escalation requirements.
- If the Context truly does not contain the answer, say:
  I couldn't find this information in the SOP.

Question:
{question}

Context:
{context}

Answer:
"""

        response = self.router.rag().invoke(prompt)

        return response.content.strip()
