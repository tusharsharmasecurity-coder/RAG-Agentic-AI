import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="YOUME@9299",
    database="delhivery_ai"
)

cursor = conn.cursor()

cursor.execute("SHOW TABLES")
print(cursor.fetchall())

cursor.execute("SELECT COUNT(*) FROM shipments")
print(cursor.fetchone())

cursor.close()
conn.close()