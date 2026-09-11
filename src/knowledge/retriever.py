import faiss
import pickle
import numpy as np

from src.memory.embedding_manager import EmbeddingManager
from src.models.router import ModelRouter

class KnowledgeRetriever:
    def __init__(self):
        self.embedding = EmbeddingManager()
        self.index = faiss.read_index("data/faiss/knowledge.faiss")
        
        with open("data/faiss/knowledge.pkl", "rb") as f:
            self.documents = pickle.load(f)
            
        self.router = ModelRouter()

    def _expand_query(self, question: str) -> list:
        """Invoked ONLY when direct vector search fails or yields poor results."""
        prompt = f"""
Rewrite this question in 2 alternative ways using formal logistics SOP terms (SOP, AWB, TAT, POD, damages):
Question: {question}

Return ONLY 2 variations, one per line.
"""
        try:
            response = self.router.chat().invoke(prompt)
            return [line.strip() for line in response.content.strip().split('\n') if line.strip()][:2]
        except Exception:
            return []

    def search(self, question: str, k: int = 3) -> list:
        # STEP 1: Fast direct search (0 extra LLM tokens)
        query_vec = np.array(self.embedding.embed_documents([question])).astype("float32")
        distances, ids = self.index.search(query_vec, k)
        
        initial_results = [self.documents[idx] for idx in ids[0] if idx != -1]

        # If direct search found enough documents, return immediately!
        if len(initial_results) >= k:
            print(f"[RAG] Direct search successful ({len(initial_results)} docs). Saved LLM expansion tokens.")
            return initial_results

        # STEP 2: Conditional Fallback (Only use LLM tokens if direct search came up short)
        print("[RAG] Low retrieval yield -> Triggering Query Expansion fallback...")
        expanded_queries = self._expand_query(question)
        
        seen_texts = set(initial_results)
        all_results = list(initial_results)

        for q in expanded_queries:
            vec = np.array(self.embedding.embed_documents([q])).astype("float32")
            _, sub_ids = self.index.search(vec, k)
            
            for idx in sub_ids[0]:
                if idx != -1:
                    doc = self.documents[idx]
                    if doc not in seen_texts:
                        seen_texts.add(doc)
                        all_results.append(doc)

        return all_results[:6]