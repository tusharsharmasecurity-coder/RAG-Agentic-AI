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
SELECT
    Status,
    COUNT(DISTINCT AWB) AS shipments
FROM shipments
WHERE Status IS NOT NULL
  AND Status <> ''
  AND Status NOT LIKE 'http%'
GROUP BY Status
ORDER BY shipments DESC
""")

print("VALID STATUS COUNT:", x.rowcount)

for row in x.fetchall():
    print(row)

c.close()
