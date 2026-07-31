import re

from src.models.router import ModelRouter

router = ModelRouter()


class SelfEvaluator:

    def evaluate(self, question: str, sql: str):

        prompt = f"""
You are an expert SQL reviewer.

User Question:
{question}

Generated SQL:
{sql}

Evaluate whether the SQL correctly answers the user's request.

Return ONLY exactly like this:

Score: 95
Decision: PASS
Reason: SQL correctly answers the question.

Do not return markdown.
"""

        response = router.chat().invoke(prompt).content

        score = re.search(r"Score:\s*(\d+)", response)
        decision = re.search(r"Decision:\s*(PASS|FAIL)", response, re.IGNORECASE)
        reason = re.search(r"Reason:\s*(.*)", response)

        return {
            "score": int(score.group(1)) if score else 0,
            "decision": decision.group(1).upper() if decision else "FAIL",
            "reason": reason.group(1).strip() if reason else "No reason",
            "raw": response,
        }