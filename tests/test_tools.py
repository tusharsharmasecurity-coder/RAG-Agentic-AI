from src.tools.sql_tool import sql_tool
from src.tools.rag_tool import rag_tool

print("=" * 50)
print("Testing SQL Tool")
print("=" * 50)

sql_result = sql_tool.invoke({"question": "Show all female users"})

print(sql_result)

print("\n" + "=" * 50)
print("Testing RAG Tool")
print("=" * 50)

rag_result = rag_tool.invoke({"question": "What is RAG?"})

print(rag_result)
