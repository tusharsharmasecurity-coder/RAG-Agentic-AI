from src.models.router import ModelRouter

router = ModelRouter()


class ResultGenerator:

    def generate(self, question, sql_result):

        prompt = f"""
You are a data analyst.

Question:
{question}

SQL Result:
{sql_result}

Rules:

- Answer ONLY from the SQL result.
- Never invent numbers.
- Never infer information.
- Never mention anything not present.
- If the SQL result is empty, say:
"No matching records were found."

Return a short professional answer.
"""

        response = router.chat().invoke(prompt)

        return response.content