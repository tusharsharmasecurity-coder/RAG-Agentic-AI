from src.database import Database


class LearningEngine:

    def __init__(self):
        self.db = Database()

    def save(
        self,
        question,
        normalized_question,
        intent,
        generated_sql,
        final_sql,
        answer,
        success,
        execution_time,
        model="llama3",
    ):

        query = """
        INSERT INTO learning_logs
        (
            question,
            normalized_question,
            intent,
            generated_sql,
            final_sql,
            answer,
            success,
            execution_time,
            model
        )
        VALUES
        (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        self.db.cursor.execute(
            query,
            (
                question,
                normalized_question,
                intent,
                generated_sql,
                final_sql,
                answer,
                success,
                execution_time,
                model,
            ),
        )

        self.db.connection.commit()
        return self.db.cursor.lastrowid

    def update_feedback(self, log_id, score):

        query = """
    UPDATE learning_logs
    SET feedback=%s
    WHERE id=%s
    """

        self.db.cursor.execute(query, (score, log_id))
        self.db.connection.commit()
