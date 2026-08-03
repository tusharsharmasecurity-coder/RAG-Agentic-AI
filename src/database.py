import mysql.connector

from src.config.settings import settings

print(">>> Database loaded from:", __file__)


class Database:

    def __init__(self):

        self.connection = mysql.connector.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
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
