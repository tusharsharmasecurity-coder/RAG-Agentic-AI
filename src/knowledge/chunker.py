from langchain_text_splitters import RecursiveCharacterTextSplitter


class KnowledgeChunker:

    def __init__(self):

        self.splitter = RecursiveCharacterTextSplitter(

            chunk_size=800,

            chunk_overlap=150

        )

    def split(self, docs):

        chunks = self.splitter.split_documents(docs)

        print(f"[INFO] Total Chunks : {len(chunks)}")

        return chunks