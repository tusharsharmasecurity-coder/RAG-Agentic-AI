import mysql.connector
from src.config import settings

user, password = settings.require_database_credentials()

conn = mysql.connector.connect(
    host=settings.db_host,
    port=settings.db_port,
    user=user,
    password=password,
    database=settings.db_name,
)

cursor = conn.cursor()

print("DATABASE:", settings.db_name)

cursor.execute("SHOW TABLES")
tables = cursor.fetchall()

print("TABLES:")
for table in tables:
    print(" -", table[0])

cursor.execute("""
    SELECT setting_key, setting_value
    FROM system_settings
""")

print("\nSYSTEM SETTINGS:")
for row in cursor.fetchall():
    print(row)

cursor.execute("SELECT COUNT(*) FROM tataunystore")

print("\nTATAUNYSTORE ROW COUNT:")
print(cursor.fetchone())

cursor.close()
conn.close()