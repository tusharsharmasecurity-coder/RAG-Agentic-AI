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
    You are a logistics SOP assistant.

      Answer the question using ONLY the information in the Context.

     Rules:
    - Do not use outside knowledge.
    - Do not guess.
    - Be concise.
    - Give at most 4 bullet points.
    - Include only information relevant to the question.

    Question:
       {question}

    Context:
    {context}

    Answer:
    """

    response = router.rag().invoke(prompt)

    return response.content
