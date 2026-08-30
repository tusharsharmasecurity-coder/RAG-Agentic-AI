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

print("\n--- STATUS CATEGORY COUNTS ---")

queries = {
    "Total": "SELECT COUNT(*) FROM shipments",

    "URL statuses":
        "SELECT COUNT(*) FROM shipments WHERE Status LIKE 'http%'",

    "Non-URL statuses":
        "SELECT COUNT(*) FROM shipments WHERE Status NOT LIKE 'http%'",

    "DTO":
        "SELECT COUNT(*) FROM shipments WHERE Status = 'DTO'",

    "Distinct non-URL statuses":
        "SELECT COUNT(DISTINCT Status) FROM shipments WHERE Status NOT LIKE 'http%'",
}

for name, query in queries.items():
    x.execute(query)
    print(f"{name}: {x.fetchone()[0]}")

print("\n--- ALL NON-URL STATUSES ---")

x.execute("""
    SELECT Status, COUNT(DISTINCT AWB) AS shipments
    FROM shipments
    WHERE Status NOT LIKE 'http%'
    GROUP BY Status
    ORDER BY shipments DESC
""")

for row in x.fetchall():
    print(row)

x.close()
c.close()
