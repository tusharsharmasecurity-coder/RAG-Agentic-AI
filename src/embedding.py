from typing import List, Any


from langchain_text_splitters import RecursiveCharacterTextSplitter


from src.memory.embedding_manager import EmbeddingManager
import numpy as np
from src.data_loader import load_all_documents

from typing import List, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter


class EmbeddingPipeline:

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embedding = EmbeddingManager(model_name)
        self.model = self.embedding.model

        print(f"[INFO] Loaded embedding model: {model_name}")

    def chunk_documents(self, documents: List[Any]) -> List[Any]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

        chunks = splitter.split_documents(documents)

        print(f"[INFO] Split {len(documents)} documents into {len(chunks)} chunks.")

        return chunks

    def embed_chunks(self, chunks: List[Any]) -> np.ndarray:
        texts = [chunk.page_content for chunk in chunks]

        print(f"[INFO] Generating embeddings for {len(texts)} chunks...")

        embeddings = self.embedding.embed_documents(texts)

        print(f"[INFO] Embeddings shape: {embeddings.shape}")

        return embeddings 


