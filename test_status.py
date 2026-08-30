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
SELECT
    Status,
    COUNT(DISTINCT AWB) AS Total_Shipments
FROM shipments
WHERE Status IS NOT NULL
  AND Status <> ''
  AND Status NOT LIKE 'http%'
GROUP BY Status
ORDER BY COUNT(DISTINCT AWB) DESC
"""

x.execute(sql)

for row in x.fetchall():
    print(row)

c.close()
