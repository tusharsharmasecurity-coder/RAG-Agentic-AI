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

x.execute("""
SELECT Status, COUNT(*)
FROM shipments
GROUP BY Status
ORDER BY COUNT(*) DESC
""")

for row in x.fetchall():
    print(row)

c.close()
