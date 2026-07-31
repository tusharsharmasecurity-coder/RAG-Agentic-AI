import os
from dotenv import load_dotenv
from src.rag_validator import RAGValidator
from src.vectorstore import FaissVectorStore
from src.data_loader import load_all_documents

from src.models.router import ModelRouter

load_dotenv()


class RAGSearch:

    def __init__(
        self,
        persist_dir="faiss_store",
        embedding_model="all-MiniLM-L6-v2",
    ):

        self.vectorstore = FaissVectorStore(persist_dir, embedding_model)

        faiss_path = os.path.join(persist_dir, "faiss.index")
        meta_path = os.path.join(persist_dir, "metadata.pkl")

        if not (os.path.exists(faiss_path) and os.path.exists(meta_path)):

            docs = load_all_documents("data")

            self.vectorstore.build_from_documents(docs)

            self.vectorstore.save()

        else:

            self.vectorstore.load()

        # Enterprise Router
        self.router = ModelRouter()
        self.validator = RAGValidator()

        print("[INFO] RAG Ready")

    def search_and_summarize(self, query, top_k=5):

        results = self.vectorstore.query(query, top_k=top_k)

        validation = self.validator.validate(results)

        print("\n========== RAG VALIDATION ==========")
        print(validation)

        if validation["decision"] == "FAIL":

            return (
                "I couldn't find relevant information " "in the uploaded SOP/documents."
            )

        context = "\n\n".join(results)

        prompt = f"""
You are a logistics assistant.

Rules:

- Answer ONLY using the supplied context.
- Never use outside knowledge.
- Never guess.
- If the context does not contain the answer,
  reply exactly:

I couldn't find this information in the uploaded documents.

Question:
{query}

Context:
{context}
"""

        response = self.router.rag().invoke(prompt)

        return response.content
