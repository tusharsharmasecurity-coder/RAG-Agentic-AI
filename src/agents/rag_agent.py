from src.knowledge.retriever import KnowledgeRetriever
from src.logger import log
import os
from langchain_ollama import ChatOllama

ollama_url = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")

# Instantiate LLM pointing directly to the host container gateway
llm = ChatOllama(
    model="llama3.2:3b",
    base_url=ollama_url,
    temperature=0
)

class RAGAgent:
    def __init__(self):
        self.retriever = KnowledgeRetriever()
        log("RAG_AGENT", "Ready")

    def ask(self, question: str):
        log("RAG_AGENT", f"Question: {question}")

        # Execute search once
        docs = self.retriever.search(question, k=3)
        extracted_texts = [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in docs
        ]
        context = "\n\n".join(extracted_texts)

        if not context.strip():
            return "I couldn't find this information in the SOP."

        prompt = f"""You are a logistics SOP assistant.

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

Answer:"""

        # FIX: Call the locally initialized ChatOllama instance directly
        response = llm.invoke(prompt)
        return response.content.strip()