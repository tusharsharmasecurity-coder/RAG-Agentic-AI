import mysql.connector

print("THIS IS THE NEW FILE")

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="YOUME@9299",
    database="companydb"
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