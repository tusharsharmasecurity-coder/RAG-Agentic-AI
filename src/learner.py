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
        planner_confidence=None,
        evaluation_score=None,
        corrected_sql=None,
        user_corrected_question=None,
    ):

        query = """
        INSERT INTO learning_logs
      (
    question,
    normalized_question,
    user_corrected_question,
    intent,
    generated_sql,
    final_sql,
    corrected_sql,
    answer,
    success,
    execution_time,
    model,
    planner_confidence,
    evaluation_score
       )
        VALUES
      (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        self.db.cursor.execute(
            query,
            (
                question,
                normalized_question,
                user_corrected_question,
                intent,
                generated_sql,
                final_sql,
                corrected_sql,
                answer,
                success,
                execution_time,
                model,
                planner_confidence,
                evaluation_score,
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

    def get_similar_examples(self, question, limit=3):

        query = """
    SELECT question, final_sql
    FROM learning_logs
    WHERE success=1
    ORDER BY created_at DESC
    LIMIT %s
    """

        self.db.cursor.execute(query, (limit,))

        return self.db.cursor.fetchall()
