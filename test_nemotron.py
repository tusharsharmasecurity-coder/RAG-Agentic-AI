from src.models.nvidia_model import nvidia_llm

llm = nvidia_llm()

prompt = """
You are an Intent Classifier.

Question:
Show total AWB

Return ONLY one word.

SQL
RAG
BOTH
CHAT
DATAFRAME
"""

response = llm.invoke(prompt)

print("==============")
print(response.content)
print("==============")