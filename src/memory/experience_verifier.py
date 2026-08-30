from src.database import Database


class ExperienceVerifier:

    TRUST_THRESHOLD = 0.90

    def __init__(self):
        self.db = Database()

    def verify(
        self,
        matched_question: str,
        sql: str,
        similarity: float,
    ) -> dict:

        if similarity < self.TRUST_THRESHOLD:
            return {
                "trusted": False,
                "reason": "low_similarity",
            }

        query = """
        SELECT
            COUNT(*) AS total,
            COALESCE(
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END),
                0
            ) AS successful,
            COALESCE(
                SUM(
                    CASE
                        WHEN feedback IS NOT NULL
                        AND feedback < 0
                        THEN 1
                        ELSE 0
                    END
                ),
                0
            ) AS negative_feedback
        FROM learning_logs
        WHERE normalized_question = %s
        AND final_sql = %s
        """

        self.db.cursor.execute(
            query,
            (matched_question, sql),
        )

        row = self.db.cursor.fetchone()

        if not row:
            return {
                "trusted": False,
                "reason": "no_learning_history",
            }

        total = int(row[0] or 0)
        successful = int(row[1] or 0)
        negative_feedback = int(row[2] or 0)

        if successful == 0:
            return {
                "trusted": False,
                "reason": "no_successful_execution",
            }

        if negative_feedback > 0:
            return {
                "trusted": False,
                "reason": "negative_feedback",
            }

        return {
            "trusted": True,
            "reason": "trusted_experience",
            "similarity": similarity,
            "total": total,
            "successful": successful,
            "negative_feedback": negative_feedback,
        }