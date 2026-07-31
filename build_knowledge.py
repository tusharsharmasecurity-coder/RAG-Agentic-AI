from src.knowledge.loader import KnowledgeLoader
from src.knowledge.chunker import KnowledgeChunker
from src.knowledge.vectorstore import KnowledgeVectorStore


loader = KnowledgeLoader()

docs = loader.load()

chunker = KnowledgeChunker()

chunks = chunker.split(docs)

store = KnowledgeVectorStore()

store.build(chunks)

print("\n✅ Knowledge Base Ready")