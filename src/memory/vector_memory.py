import os
import faiss
import numpy as np
from src.memory.question_normalizer import normalize
from src.memory.embedding_manager import EmbeddingManager
import pickle


class VectorMemory:

    def __init__(self):

     self.embedding = EmbeddingManager()

     self.dimension = 384

     self.memory_path = "data/memory"

     os.makedirs(self.memory_path, exist_ok=True)

     self.index_file = os.path.join(
        self.memory_path,
        "memory.faiss"
     )

     self.question_file = os.path.join(
        self.memory_path,
        "questions.pkl"
     )

     self.load_memory()
    def load_memory(self):

     if os.path.exists(self.index_file):

        self.index = faiss.read_index(
            self.index_file
        )

        with open(
            self.question_file,
            "rb"
        ) as f:

            self.questions = pickle.load(f)

        print(
            f"[Memory] Loaded {len(self.questions)} questions."
        )

     else:

        self.index = faiss.IndexFlatIP(
            self.dimension
        )

        self.questions = []

        print("[Memory] New memory created.")
    def save_memory(self):

     faiss.write_index(
        self.index,
        self.index_file
     )

     with open(
        self.question_file,
        "wb"
     ) as f:

        pickle.dump(
            self.questions,
            f
        )    
    # -------------------------

    def add(self, question):

        question = normalize(question)

        vector = self.embedding.embed(question)

        self.index.add(
            np.array([vector]).astype("float32")
        )

        self.questions.append(question)
        self.save_memory()

    # -------------------------

    def search(self, question):

        question = normalize(question)

        if len(self.questions) == 0:
            return None, 0

        vector = self.embedding.embed(question)

        scores, ids = self.index.search(
            np.array([vector]).astype("float32"),
            1
        )

        score = float(scores[0][0])

        idx = int(ids[0][0])

        if score < 0.80:
            return None, score

        return self.questions[idx], score