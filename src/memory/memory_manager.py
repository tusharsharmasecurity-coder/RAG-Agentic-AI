import os

import redis

from src.memory.vector_memory import VectorMemory
from src.database import Database


class MemoryManager:

    def __init__(self):

        # Existing FAISS semantic memory
        self.vector = VectorMemory()

        # Existing MySQL memory
        self.db = Database()

        # Redis configuration
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_ttl = int(os.getenv("REDIS_MEMORY_TTL", "86400"))

        self.redis = None

        try:

            self.redis = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1,
            )

            self.redis.ping()

            print(f"[Redis] Connected: " f"{self.redis_host}:{self.redis_port}")

        except redis.RedisError as exc:

            # Redis should never bring the application down.
            self.redis = None

            print(f"[Redis] Unavailable: {exc}")

    # ============================================================
    # REDIS KEY
    # ============================================================

    @staticmethod
    def _redis_key(question: str) -> str:
        return f"rag:sql:{question}"

    # ============================================================
    # SAVE SQL
    # ============================================================

    def save_sql(
        self,
        question,
        sql,
        execution_time=0,
    ):

        # --------------------------------------------------------
        # 1. FAISS MEMORY
        # --------------------------------------------------------

        self.vector.add(question)

        # --------------------------------------------------------
        # 2. MYSQL MEMORY
        # --------------------------------------------------------

        query = """
        INSERT INTO ai_memory
        (question_pattern, sql_query)
        VALUES (%s, %s)
        """

        self.db.cursor.execute(
            query,
            (question, sql),
        )

        self.db.connection.commit()

        # --------------------------------------------------------
        # 3. REDIS CACHE
        # --------------------------------------------------------

        if self.redis is not None:

            try:

                key = self._redis_key(question)

                self.redis.setex(
                    key,
                    self.redis_ttl,
                    sql,
                )

                print("[Redis] SQL cached")

            except redis.RedisError as exc:

                print(f"[Redis] Cache write failed: {exc}")

    # ============================================================
    # SEARCH SQL
    # ============================================================

    def search(self, question):

        # --------------------------------------------------------
        # 1. REDIS FAST PATH
        # --------------------------------------------------------

        if self.redis is not None:

            try:
                key = self._redis_key(question)
                cached_sql = self.redis.get(key)

                if cached_sql:
                    print("[Redis] Cache HIT")

                    return {
                        "sql": cached_sql,
                        "matched_question": question,
                        "similarity": 1.0,
                        "source": "redis",
                    }

            except redis.RedisError as exc:
                print(f"[Redis] Cache read failed: {exc}")

        # --------------------------------------------------------
        # 2. FAISS SEMANTIC MEMORY
        # --------------------------------------------------------

        similar, score = self.vector.search(question)

        if similar is None:
            return None

        # --------------------------------------------------------
        # 3. MYSQL MEMORY
        # --------------------------------------------------------

        query = """
    SELECT sql_query
    FROM ai_memory
    WHERE question_pattern=%s
    LIMIT 1
    """

        self.db.cursor.execute(
            query,
            (similar,),
        )

        row = self.db.cursor.fetchone()

        if not row:
            return None

        sql = row[0]

        # --------------------------------------------------------
        # 4. PROMOTE TO REDIS
        # --------------------------------------------------------

        if self.redis is not None:

            try:
                key = self._redis_key(question)

                self.redis.setex(
                    key,
                    self.redis_ttl,
                    sql,
                )

                print("[Redis] SQL promoted to cache")

            except redis.RedisError as exc:

                print(f"[Redis] Cache promotion failed: {exc}")

        return {
            "sql": sql,
            "matched_question": similar,
            "similarity": score,
            "source": "faiss",
        }
