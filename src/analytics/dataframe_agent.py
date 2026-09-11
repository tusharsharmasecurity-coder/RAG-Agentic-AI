import re
import pandas as pd
from src.analytics.dataframe_memory import dataframe_memory
from src.models.router import ModelRouter

class DataFrameAgent:
    def __init__(self):
        self.router = ModelRouter()

    def run(self, question):
        # 1. Get the current spreadsheet (DataFrame) from memory
        df = dataframe_memory.get()
        
        if df is None:
            return {
                "answer": "No active dataset. Please run a SQL query first.", 
                "dataframe": None
            }

        # ---------------------------------------------------------
        # PANDAS LEARNING MOMENT:
        # df.columns -> gives us the names of the columns
        # df.dtypes -> tells us if a column is text, numbers, or dates
        # df.head(3) -> grabs just the first 3 rows of the data
        # We send this to the LLM so it knows exactly what the data looks like!
        # ---------------------------------------------------------
        context = f"""
        Columns: {list(df.columns)}
        Data Types: {df.dtypes.to_dict()}
        Sample Data (first 3 rows):
        {df.head(3).to_string()}
        """

        prompt = f"""
You are a Python Data Analyst. You have a pandas DataFrame named `df`.
Here is what `df` looks like:
{context}

User Question: {question}

Write Python pandas code to answer the user's question.

STRICT RULES:
1. ONLY use pandas. 
2. Do not use print().
3. Save the final modified DataFrame to a variable named `result_df`.
4. Save a short text explanation to a variable named `summary`.
5. Return ONLY the python code inside ```python ``` blocks.

Example:
```python
result_df = df.sort_values(by='Total', ascending=False)
summary = "I sorted the data by Total in descending order."
"""