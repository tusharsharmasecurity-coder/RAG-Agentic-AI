from src.memory.vector_memory import VectorMemory
from src.database import Database


class MemoryManager:

    def __init__(self):
        self.vector = VectorMemory()
        self.db = Database()

    # -------------------------
    # Save SQL
    # -------------------------
    def save_sql(self, question, sql, execution_time=0):

        self.vector.add(question)

        query = """
        INSERT INTO ai_memory
        (question_pattern, sql_query)
        VALUES (%s, %s)
        """

        self.db.cursor.execute(
            query,
            (question, sql)
        )

        self.db.connection.commit()

    # -------------------------
    # Search SQL
    # -------------------------
    def search(self, question):

        similar, score = self.vector.search(question)

        if similar is None:
            return None

        query = """
        SELECT sql_query
        FROM ai_memory
        WHERE question_pattern=%s
        LIMIT 1
        """

        self.db.cursor.execute(
            query,
            (similar,)
        )

        row = self.db.cursor.fetchone()

        if row:
            return row[0]

        return None