import mysql.connector
from src.config import settings

c = mysql.connector.connect(
    host=settings.db_host,
    port=settings.db_port,
    user=settings.db_user,
    password=settings.db_password,
    database=settings.db_name,
)

x = c.cursor()

sql = """
DELETE FROM ai_memory
WHERE question_pattern = 'how many shipments are there by Status'
"""

x.execute(sql)
c.commit()

print("Deleted:", x.rowcount)

c.close()
