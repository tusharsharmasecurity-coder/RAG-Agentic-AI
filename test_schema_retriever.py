from src.schema.schema_retriever import SchemaRetriever

retriever = SchemaRetriever()

question = "how many customer cut the call in ajio"

tables = retriever.retrieve(question)

print("\nRelevant Schema\n")

for table in tables:

    print(table)