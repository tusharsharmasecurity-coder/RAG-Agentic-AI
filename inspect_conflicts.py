import mysql.connector
from src.config import settings

c = mysql.connector.connect(
    host=settings.db_host,
    port=settings.db_port,
    user=settings.db_user,
    password=settings.db_password,
    database=settings.db_name,
)

x = c.cursor(dictionary=True)

questions = (
    "how many shipments are there by Status",
    "how many unique awbs are there in each year",
    "how many months are present in the data",
    "how many AWB statuses are present",
    "what is the average AWB age",
)

placeholders = ",".join(["%s"] * len(questions))

sql = f"""
SELECT normalized_question, final_sql, COUNT(1) AS n
FROM learning_logs
WHERE normalized_question IN ({placeholders})
GROUP BY normalized_question, final_sql
ORDER BY normalized_question, n DESC
"""

x.execute(sql, questions)

for r in x.fetchall():
    print("\nQUESTION:", r["normalized_question"])
    print("COUNT:", r["n"])
    print("SQL:", r["final_sql"])

c.close()
