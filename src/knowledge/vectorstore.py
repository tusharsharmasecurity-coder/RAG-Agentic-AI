import os
import pickle
import faiss
import numpy as np

from src.memory.embedding_manager import EmbeddingManager


class KnowledgeVectorStore:

    def __init__(self):

        self.embedding = EmbeddingManager()

        self.dimension = 384

        self.store_path = "data/faiss"

        os.makedirs(self.store_path, exist_ok=True)

        self.index_path = os.path.join(
            self.store_path,
            "knowledge.faiss"
        )

        self.meta_path = os.path.join(
            self.store_path,
            "knowledge.pkl"
        )

    def build(self, chunks):

        texts = [c.page_content for c in chunks]

        embeddings = self.embedding.embed_documents(texts)

        index = faiss.IndexFlatIP(self.dimension)

        index.add(
            np.array(embeddings).astype("float32")
        )

        faiss.write_index(index, self.index_path)

        with open(self.meta_path, "wb") as f:

            pickle.dump(texts, f)

        print(f"[INFO] Saved {len(texts)} chunks.")