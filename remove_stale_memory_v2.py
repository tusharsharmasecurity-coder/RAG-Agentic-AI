import os
import pickle
import faiss
import numpy as np
import mysql.connector

from src.config import settings
from src.memory.question_normalizer import normalize
from src.memory.embedding_manager import EmbeddingManager


TARGET = "how many shipments are there by current status"

MEMORY_PATH = "data/memory"
INDEX_FILE = os.path.join(
    MEMORY_PATH,
    "memory.faiss",
)
QUESTION_FILE = os.path.join(
    MEMORY_PATH,
    "questions.pkl",
)


# ============================================================
# NORMALIZED TARGET
# ============================================================

target_normalized = normalize(TARGET)

print("\n========== STALE MEMORY CLEANUP ==========")

print("Target:")
print(repr(TARGET))

print("Normalized target:")
print(repr(target_normalized))


# ============================================================
# MYSQL
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
    SELECT question_pattern
    FROM ai_memory
    """
)

rows = cursor.fetchall()

print("\nExisting MySQL memories:", len(rows))


# ============================================================
# FIND + DELETE STALE MEMORY
# ============================================================

removed = 0
remaining_questions = []

for row in rows:

    question = row[0]

    normalized = normalize(question)

    if normalized == target_normalized:

        print("\n[REMOVE] Stale memory:")
        print("Raw       :", repr(question))
        print("Normalized:", repr(normalized))

        cursor.execute(
            """
            DELETE FROM ai_memory
            WHERE question_pattern = %s
            """,
            (question,),
        )

        removed += cursor.rowcount

    else:

        remaining_questions.append(question)


connection.commit()

print("\n[MYSQL] Removed:", removed)

cursor.close()
connection.close()


# ============================================================
# REBUILD FAISS
# ============================================================

print("\n========== REBUILDING FAISS ==========")

embedding = EmbeddingManager()

index = faiss.IndexFlatIP(384)

questions = []

for question in remaining_questions:

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
print("[FAISS] Remaining questions:", len(questions))


# ============================================================
# VERIFY
# ============================================================

print("\n========== FINAL VERIFICATION ==========")

target_found = target_normalized in questions

if target_found:

    print("[ERROR] Stale target STILL exists!")

else:

    print("[OK] Stale target removed from FAISS.")


print("\nRemaining FAISS questions:")

for question in questions:

    print("  ", question)