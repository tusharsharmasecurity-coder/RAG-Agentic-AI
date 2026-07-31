from src.models.router import ModelRouter

router = ModelRouter()


class SQLSelfHealer:

    def heal(self, question, sql, error, schema):

        prompt = f"""
You are an expert MySQL SQL engineer.

Question:
{question}

Bad SQL:
{sql}

Error:
{error}

Schema:
{schema}

Fix the SQL and return ONLY a valid MySQL SELECT query.
Do not explain.
Do not use markdown.
"""

        response = router.sql().invoke(prompt)
        fixed_sql = response.content.strip()

        fixed_sql = fixed_sql.replace("```sql", "")
        fixed_sql = fixed_sql.replace("```", "")

        return fixed_sql