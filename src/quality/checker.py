from src.models.router import ModelRouter


class QualityChecker:

    def __init__(self):

        self.router = ModelRouter()

    def evaluate(
        self,
        question,
        answer,
        sql="",
        rag=""
    ):

        prompt = f"""
You are an AI Quality Judge.

User Question:
{question}

Generated SQL:
{sql}

RAG Context:
{rag}

Final Answer:
{answer}

Evaluate:

1. Is the answer correct?
2. Is anything missing?
3. Any hallucination?
4. Confidence (0-100)

Return ONLY JSON.

Example:

{{
    "confidence":95,
    "decision":"ACCEPT",
    "reason":"Answer fully matches."
}}

Decision must be either:

ACCEPT
RETRY
"""

        response = self.router.chat().invoke(prompt)

        return response.content