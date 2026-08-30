import mysql.connector

from src.config import settings


class Database:

    def __init__(self):

        user, password = settings.require_database_credentials()

        self.connection = mysql.connector.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=user,
            password=password,
            database=settings.db_name,
            connection_timeout=10,
            autocommit=True,
        )

        self.cursor = self.connection.cursor()


    def _ensure_connection(self):

        if not self.connection.is_connected():

            self.connection.reconnect(
                attempts=3,
                delay=1,
            )

            self.cursor = self.connection.cursor()


    def execute(self, query):

        self._ensure_connection()

        self.cursor.execute(query)

        return self.cursor.fetchall()


    def execute_one(self, query):

        self._ensure_connection()

        self.cursor.execute(query)

        return self.cursor.fetchone()


    def close(self):

        try:
            self.cursor.close()
        except Exception:
            pass

        try:
            self.connection.close()
        except Exception:
            pass