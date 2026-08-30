import mysql.connector
from src.config import settings

print("THIS IS THE NEW FILE")

user, password = settings.require_database_credentials()
conn = mysql.connector.connect(
    host=settings.db_host, port=settings.db_port, user=user, password=password,
    database=settings.db_name,
)

print("✅ Connected Successfully!")

cursor = conn.cursor()

# Read all records
cursor.execute("SELECT * FROM user_details")

rows = cursor.fetchall()

print(f"Total Rows: {len(rows)}")

# Print first 10 rows
for row in rows[:10]:
    print(row)

cursor.close()
conn.close()
