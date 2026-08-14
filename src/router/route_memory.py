from src.database import Database
from src.logger import log
from src.text_normalizer import normalize


class RouteMemory:
    VALID_INTENTS = {"SQL", "RAG", "BOTH", "DATAFRAME", "CHAT"}

    def __init__(self, database=None):
        self.db = database or Database()
        self._ensure_table()

    def _ensure_table(self):
        self.db.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS route_memory (
                id BIGINT NOT NULL AUTO_INCREMENT,
                question TEXT NOT NULL,
                normalized_question VARCHAR(512) NOT NULL,
                intent VARCHAR(16) NOT NULL,
                confidence DECIMAL(5,4) NOT NULL,
                method VARCHAR(16) NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id),
                UNIQUE KEY uq_route_memory_normalized_question (normalized_question)
            ) ENGINE=InnoDB
            """
        )
        self.db.connection.commit()

    def find(self, question):
        normalized_question = normalize(question)

        self.db.cursor.execute(
            """
            SELECT intent, confidence, method
            FROM route_memory
            WHERE normalized_question = %s
            LIMIT 1
            """,
            (normalized_question,),
        )
        record = self.db.cursor.fetchone()

        if record is None:
            log("ROUTE_MEMORY", f"MISS normalized_question={normalized_question}")
            return None

        intent, confidence, method = record

        if intent not in self.VALID_INTENTS:
            log("ROUTE_MEMORY", f"SKIP invalid stored intent={intent}")
            return None

        log(
            "ROUTE_MEMORY",
            f"HIT intent={intent} method={method} score={float(confidence)}",
        )
        return {
            "intent": intent,
            "confidence": float(confidence),
            "method": method,
        }

    def save(self, question, intent, confidence, method):
        if intent not in self.VALID_INTENTS:
            log("ROUTE_MEMORY", f"SKIP invalid intent={intent}")
            return False

        if not isinstance(confidence, (int, float)) or confidence <= 0:
            log("ROUTE_MEMORY", f"SKIP unresolved confidence={confidence}")
            return False

        normalized_question = normalize(question)

        if not normalized_question:
            log("ROUTE_MEMORY", "SKIP empty normalized question")
            return False

        self.db.cursor.execute(
            """
            INSERT INTO route_memory
                (question, normalized_question, intent, confidence, method)
            VALUES
                (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                question = VALUES(question),
                intent = VALUES(intent),
                confidence = VALUES(confidence),
                method = VALUES(method)
            """,
            (question, normalized_question, intent, confidence, method),
        )
        self.db.connection.commit()
        log(
            "ROUTE_MEMORY",
            f"SAVE intent={intent} method={method} score={confidence}",
        )
        return True
