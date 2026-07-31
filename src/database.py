import mysql.connector
print(">>> Database loaded from:", __file__)

class Database:

    def __init__(self):

        self.connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="YOUME@9299",
            database="delhivery_ai"
        )

        self.cursor = self.connection.cursor()

        # Debug
        self.cursor.execute("SELECT DATABASE()")
        print("Current Database:", self.cursor.fetchone())

        self.cursor.execute("SHOW TABLES")
        print("Tables:", self.cursor.fetchall())

        print("[INFO] Database Connected")

    def execute(self, query):

        self.cursor.execute(query)

        return self.cursor.fetchall()
    def execute_one(self, query):
        self.cursor.execute(query)
        return self.cursor.fetchone()

    def close(self):

        self.cursor.close()
        self.connection.close()