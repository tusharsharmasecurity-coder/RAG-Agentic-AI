import os
import pickle
import faiss
import numpy as np

from src.memory.embedding_manager import EmbeddingManager
from src.memory.question_normalizer import normalize

MEMORY_PATH = "data/memory"
INDEX_FILE = os.path.join(MEMORY_PATH, "memory.faiss")
QUESTION_FILE = os.path.join(MEMORY_PATH, "questions.pkl")

TARGET = normalize("how many shipments are there by current status")

print("Target:", TARGET)

with open(QUESTION_FILE, "rb") as f:
    questions = pickle.load(f)

print("Existing questions:", len(questions))

remaining = [
    q for q in questions
    if normalize(q) != TARGET
]

removed = len(questions) - len(remaining)

print("Removed:", removed)
print("Remaining:", len(remaining))

if removed == 0:
    print("Nothing removed. FAISS memory unchanged.")
    raise SystemExit(0)

embedding = EmbeddingManager()

dimension = 384

index = faiss.IndexFlatIP(dimension)

vectors = []

for question in remaining:
    vector = embedding.embed(question)
    vectors.append(vector)

if vectors:
    index.add(
        np.array(vectors).astype("float32")
    )

faiss.write_index(index, INDEX_FILE)

with open(QUESTION_FILE, "wb") as f:
    pickle.dump(remaining, f)

print("FAISS memory rebuilt successfully.")
print("Questions:", len(remaining))
