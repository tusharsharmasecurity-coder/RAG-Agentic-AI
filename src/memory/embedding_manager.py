from sentence_transformers import SentenceTransformer


class EmbeddingManager:

    def __init__(self):

        self.model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

    def embed(self, text):

        return self.model.encode(
            text,
            normalize_embeddings=True
        )
    def embed_documents(self, texts):

     return self.model.encode(
        texts,
        normalize_embeddings=True
    )