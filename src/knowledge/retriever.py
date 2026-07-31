import faiss
import pickle
import numpy as np

from src.memory.embedding_manager import EmbeddingManager


class KnowledgeRetriever:

    def __init__(self):

        self.embedding = EmbeddingManager()

        self.index = faiss.read_index("data/faiss/knowledge.faiss")

        with open("data/faiss/knowledge.pkl", "rb") as f:

            self.documents = pickle.load(f)

    def search(self, question, k=5):

        query = self.embedding.embed_documents([question])

        query = np.array(query).astype("float32")

        scores, ids = self.index.search(query, k)

        results = []

        for idx in ids[0]:

            if idx != -1:

                results.append(self.documents[idx])

        return results
