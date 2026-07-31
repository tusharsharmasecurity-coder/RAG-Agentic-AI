from langchain.tools import tool

from src.knowledge.retriever import KnowledgeRetriever
from src.models.router import ModelRouter

router = ModelRouter()


retriever = KnowledgeRetriever()


@tool
def rag_tool(question: str):
    """
    Use this tool whenever the user asks about SOPs,
    company policies, warehouse procedures,
    validation process, closure process,
    documentation or operational guidelines.
    """

    docs = retriever.search(question)

    context = "\n\n".join(docs)

    prompt = f"""
You are Delhivery AI.

Answer ONLY from the provided context.

If the answer is not found, say:
'I couldn't find this information in the SOP.'

Context:
{context}

Question:
{question}
"""

    response = router.rag().invoke(prompt)

    return response.content