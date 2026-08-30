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

print("\n--- STATUS SAMPLES ---")
x.execute("SELECT AWB, Status FROM shipments LIMIT 20")
for r in x.fetchall():
    print(r)

print("\n--- PRODUCT IMAGE SAMPLES ---")
x.execute("""
    SELECT AWB, `Product Images`
    FROM shipments
    WHERE `Product Images` IS NOT NULL
      AND `Product Images` <> ''
    LIMIT 5
""")
for r in x.fetchall():
    print(r)

print("\n--- URL STATUS SAMPLES ---")
x.execute("""
    SELECT AWB, Status
    FROM shipments
    WHERE Status LIKE 'http%'
    LIMIT 10
""")
for r in x.fetchall():
    print(r)

x.close()
c.close()
