import os
import faiss
import numpy as np
import pickle
from typing import List,Any
from sentence_transformers import SentenceTransformer
from src.embedding import EmbeddingPipeline

import os
from typing import List, Any
import numpy as np
from sentence_transformers import SentenceTransformer


class FaissVectorStore:

    def __init__(
        self,
        persist_dir: str = "faiss_store",
        embedding_model: str = "all-MiniLM-L6-v2",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        self.persist_dir = persist_dir
        os.makedirs(self.persist_dir, exist_ok=True)

        self.index = None
        self.metadata = []

        self.embedding_model = embedding_model
        self.model = SentenceTransformer(embedding_model)

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        print(f"[INFO] Loaded embedding model: {embedding_model}")

    def build_from_documents(self, documents: List[Any]):
        print(f"[INFO] Building vector store from {len(documents)} raw documents...")

        emb_pipe = EmbeddingPipeline(
            model_name=self.embedding_model,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )

        # Split into chunks
        chunks = emb_pipe.chunk_documents(documents)

        # Generate embeddings
        embeddings = emb_pipe.embed_chunks(chunks)

        # Store metadata
        metadatas = [
            {"text": chunk.page_content}
            for chunk in chunks
        ]

        # Add embeddings to FAISS
        self.add_embeddings(
            np.array(embeddings).astype("float32"),
            metadatas
        )
        self.save()  

    def add_embeddings(self, embeddings: np.ndarray, metadatas: List[Any] = None):
        dim = embeddings.shape[1]

        if self.index is None:
            self.index = faiss.IndexFlatL2(dim)

        self.index.add(embeddings)

        if metadatas:
            self.metadata.extend(metadatas)

        print(f"[INFO] Added {embeddings.shape[0]} vectors to Faiss index.")

    def save(self):
        faiss_path = os.path.join(self.persist_dir, "faiss.index")
        meta_path = os.path.join(self.persist_dir, "metadata.pkl")

        faiss.write_index(self.index, faiss_path)

        with open(meta_path, "wb") as f:
            pickle.dump(self.metadata, f)

        print(f"[INFO] Saved Faiss index and metadata to {self.persist_dir}")

    def load(self):
        faiss_path = os.path.join(self.persist_dir, "faiss.index")
        meta_path = os.path.join(self.persist_dir, "metadata.pkl")

        if not os.path.exists(faiss_path):
            raise FileNotFoundError("Faiss index not found.")

        self.index = faiss.read_index(faiss_path)

        with open(meta_path, "rb") as f:
            self.metadata = pickle.load(f)

        print(f"[INFO] Loaded Faiss index with {self.index.ntotal} vectors.")

    def query(self, question: str, top_k: int = 3):
    # Convert the question into an embedding
     query_embedding = self.model.encode([question]).astype("float32")

    # Search the FAISS index
     distances, indices = self.index.search(query_embedding, top_k)

     results = []

     for idx in indices[0]:
        if idx != -1:
            results.append(self.metadata[idx]["text"])

     return results