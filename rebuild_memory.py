import os
import pickle
import faiss
import numpy as np
import mysql.connector

from src.config import settings
from src.memory.question_normalizer import normalize
from src.memory.embedding_manager import EmbeddingManager


TARGET = "how many shipments are there by Status"

MEMORY_PATH = "data/memory"
INDEX_FILE = os.path.join(MEMORY_PATH, "memory.faiss")
QUESTION_FILE = os.path.join(MEMORY_PATH, "questions.pkl")


print("\n========== CLEANING STALE MEMORY ==========")

# ============================================================
# 1. REMOVE TARGET FROM MYSQL MEMORY
# ============================================================

connection = mysql.connector.connect(
    host=settings.db_host,
    port=settings.db_port,
    user=settings.db_user,
    password=settings.db_password,
    database=settings.db_name,
)

cursor = connection.cursor()

cursor.execute(
    """
    DELETE FROM ai_memory
    WHERE question_pattern = %s
    """,
    (TARGET,),
)

print("[MYSQL] Deleted rows:", cursor.rowcount)

connection.commit()

# Show remaining memory
cursor.execute(
    """
    SELECT question_pattern
    FROM ai_memory
    """
)

db_questions = [row[0] for row in cursor.fetchall()]

print("[MYSQL] Remaining questions:", len(db_questions))

for q in db_questions:
    print("  ", q)

cursor.close()
connection.close()


# ============================================================
# 2. REBUILD FAISS FROM MYSQL MEMORY
# ============================================================

print("\n========== REBUILDING FAISS ==========")

os.makedirs(MEMORY_PATH, exist_ok=True)

embedding = EmbeddingManager()

dimension = 384

index = faiss.IndexFlatIP(dimension)

questions = []

for question in db_questions:

    normalized = normalize(question)

    vector = embedding.embed(normalized)

    index.add(
        np.array(
            [vector],
            dtype="float32",
        )
    )

    questions.append(normalized)


faiss.write_index(
    index,
    INDEX_FILE,
)

with open(
    QUESTION_FILE,
    "wb",
) as f:

    pickle.dump(
        questions,
        f,
    )


print("[FAISS] Rebuilt successfully")
print("[FAISS] Questions:", len(questions))


# ============================================================
# 3. VERIFY TARGET IS GONE
# ============================================================

print("\n========== VERIFICATION ==========")

if TARGET in questions:

    print("[ERROR] Target still exists in FAISS!")

else:

    print("[OK] Stale target removed from FAISS")


print("\nMemory cleanup complete.")