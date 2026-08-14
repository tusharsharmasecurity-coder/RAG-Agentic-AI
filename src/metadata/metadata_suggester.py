from src.models.router import ModelRouter
import json


class MetadataSuggester:

    def __init__(self):
        self.router = ModelRouter()

    def suggest(self, column_name):

        prompt = f"""
You are a logistics metadata expert.

A new uploaded file contains this column:

{column_name}

Your task is to predict its business meaning.

Return ONLY valid JSON.

Example:

{{
    "column":"GW",
    "suggestions":[
        {{
            "business_name":"Gross Weight",
            "confidence":96
        }},
        {{
            "business_name":"Gateway",
            "confidence":70
        }},
        {{
            "business_name":"Group Weight",
            "confidence":41
        }}
    ]
}}

Rules

- Maximum 3 suggestions
- Confidence between 0-100
- Highest confidence first
- Return ONLY JSON
"""

        response = self.router.chat().invoke(prompt)

        try:
            return json.loads(response.content)

        except Exception:

            return {
                "column": column_name,
                "suggestions": [
                    {
                        "business_name": "Unknown",
                        "confidence": 0
                    }
                ]
            }