from src.memory.vector_memory import VectorMemory
from src.database import Database


class MemoryManager:

    def __init__(self):
        self.vector = VectorMemory()
        self.db = Database()

    # -------------------------
    # Save SQL
    # -------------------------
    def save_sql(
        self,
        question,
        sql,
        answer=None,
        log_id=None,
        execution_time=0,
    ):

        self.vector.add(
            question=question,
            sql=sql,
            answer=answer,
            log_id=log_id,
        )

        query = """
        INSERT INTO ai_memory
        (question_pattern, sql_query)
        VALUES (%s, %s)
        """

        self.db.cursor.execute(query, (question, sql))

        self.db.connection.commit()

    # -------------------------
    # Search SQL
    # -------------------------
    def search(self, question):

        memory = self.vector.search(question)

        if memory is None:
            return None

        return memory  # ✅ Return the whole dictionary
