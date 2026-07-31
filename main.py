from src.search import RAGSearch


def main():

    rag = RAGSearch()

    while True:

        query = input("\nAsk a question (type 'exit' to quit): ")

        if query.lower() == "exit":
            break

        answer = rag.search_and_summarize(
            query=query,
            top_k=3
        )

        print("\nAnswer:\n")
        print(answer)


if __name__ == "__main__":
    main()