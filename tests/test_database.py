from src.database import Database

db = Database()

rows = db.execute(
    "SELECT * FROM user_details LIMIT 5"
)

for row in rows:
    print(row)

db.close()