from src.data_loader import load_all_documents
from src.vectorstore import FaissVectorStore


def main():

    print("Loading documents...")

    docs = load_all_documents("data")

    print(f"Loaded {len(docs)} documents")

    store = FaissVectorStore("faiss_store")

    store.build_from_documents(docs)

    store.save()

    print("\n✅ Vector Store Created Successfully!")


if __name__ == "__main__":
    main()