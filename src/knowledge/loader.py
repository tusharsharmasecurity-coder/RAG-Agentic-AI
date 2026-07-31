from pathlib import Path

from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
)


class KnowledgeLoader:

    def __init__(self, folder="data/knowledge_base"):

        self.folder = Path(folder)

    def load(self):

        documents = []

        # PDFs
        for pdf in self.folder.rglob("*.pdf"):

            loader = PyPDFLoader(str(pdf))

            documents.extend(loader.load())

        # Word Files
        for doc in self.folder.rglob("*.docx"):

            loader = Docx2txtLoader(str(doc))

            documents.extend(loader.load())

        print(f"[INFO] Loaded {len(documents)} documents")

        return documents