import mysql.connector

from src.config import settings
from src.memory.question_normalizer import normalize


TARGET = "how many shipments are there by current status"

connection = mysql.connector.connect(
    host=settings.db_host,
    port=settings.db_port,
    user=settings.db_user,
    password=settings.db_password,
    database=settings.db_name,
)

cursor = connection.cursor()

cursor.execute(
    """
    SELECT question_pattern
    FROM ai_memory
    WHERE LOWER(question_pattern) LIKE '%how many shipments%'
    """
)

rows = cursor.fetchall()

print("\n========== MEMORY TARGET DIAGNOSTIC ==========")

print("Target:")
print(repr(TARGET))
print("Normalized target:")
print(repr(normalize(TARGET)))

print("\nDatabase matches:")

for row in rows:
    value = row[0]

    print("\nRAW:")
    print(repr(value))

    print("NORMALIZED:")
    print(repr(normalize(value)))

    print("RAW EQUAL:", value == TARGET)
    print(
        "NORMALIZED EQUAL:",
        normalize(value) == normalize(TARGET),
    )

cursor.close()
connection.close()