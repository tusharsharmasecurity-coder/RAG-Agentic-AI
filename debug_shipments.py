import mysql.connector
from src.config import settings


conn = mysql.connector.connect(
    host=settings.db_host,
    port=settings.db_port,
    user=settings.db_user,
    password=settings.db_password,
    database=settings.db_name,
)

cursor = conn.cursor()

print("\nSHIPMENT DATA CHECK")
print("-" * 50)

# 1. Total rows
cursor.execute("SELECT COUNT(*) FROM shipments")
print("Total rows:", cursor.fetchone()[0])

# 2. Distinct AWBs
cursor.execute("SELECT COUNT(DISTINCT AWB) FROM shipments")
print("Distinct AWB:", cursor.fetchone()[0])

# 3. Distinct statuses
cursor.execute("SELECT COUNT(DISTINCT Status) FROM shipments")
print("Distinct statuses:", cursor.fetchone()[0])

# 4. URL statuses
cursor.execute(
    "SELECT COUNT(*) FROM shipments WHERE Status LIKE 'http%'"
)
print("URL statuses:", cursor.fetchone()[0])

# 5. NULL statuses
cursor.execute(
    "SELECT COUNT(*) FROM shipments WHERE Status IS NULL"
)
print("NULL statuses:", cursor.fetchone()[0])

# 6. Clean status values
print("\nCLEAN STATUSES")
print("-" * 50)

cursor.execute("""
    SELECT
        Status,
        COUNT(DISTINCT AWB) AS shipment_count
    FROM shipments
    WHERE Status IS NOT NULL
      AND Status NOT LIKE 'http%'
    GROUP BY Status
    ORDER BY shipment_count DESC
""")

for status, count in cursor.fetchall():
    print(f"{status}: {count}")

cursor.close()
conn.close()