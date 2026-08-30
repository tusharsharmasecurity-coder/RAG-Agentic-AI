from sentence_transformers import SentenceTransformer
import torch

from src.config import settings


def embedding_device() -> str:
    """
    Determine the embedding device.

    Priority:
    1. Explicit CPU request
    2. Explicit CUDA request when CUDA is available
    3. Automatic CUDA -> CPU fallback
    """

    requested = settings.embedding_device.lower()

    if requested == "cpu":
        return "cpu"

    if requested == "cuda":
        return "cuda" if torch.cuda.is_available() else "cpu"

    return "cuda" if torch.cuda.is_available() else "cpu"


class EmbeddingManager:

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
    ) -> None:

        self.device = embedding_device()

        print(f"[EMBEDDING] Device: {self.device}")

        # Load directly onto the selected device.
        # This avoids CPU -> CUDA .to() after model construction.
        self.model = SentenceTransformer(
            model_name,
            device=self.device,
        )

        print(
            f"[EMBEDDING] Model loaded: {model_name} "
            f"on {self.device}"
        )

    def embed(self, text):

        return self.model.encode(
            text,
            normalize_embeddings=True,
        )

    def embed_documents(self, texts):

        return self.model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=settings.embedding_batch_size,
            show_progress_bar=False,
        )