from src.models.router import ModelRouter
from src.planner_validator import PlannerValidator

router = ModelRouter()

from src.logger import log


class Planner:
    def __init__(self):
        self.validator = PlannerValidator()

    def plan(self, question, context=""):

        prompt = f"""
You are an Intent Classifier.

Conversation:
{context}

User Question:
{question}

Choose ONLY ONE of these labels.

SQL
- Counts
- Sum
- Average
- Max
- Min
- Warehouse
- Shipment
- AWB
- Tracking
- Customer
- Database

RAG
- SOP
- Policy
- Documentation
- Process
- Manual
- Guidelines

BOTH
- Needs SQL and SOP together.

DATAFRAME
ONLY if the user refers to an EXISTING SQL RESULT.

Examples:
Sort this
Filter this
Top 10
Plot this
Average of this
Show only delayed
Group this result

CHAT
Greetings
Hello
Hi
Thanks
Bye
General conversation

VERY IMPORTANT

Question:
Show total AWB by warehouse

Answer:
SQL

Question:
Explain closure process

Answer:
RAG

Question:
Show total AWB by warehouse and explain closure process

Answer:
BOTH

Question:
Sort this result

Answer:
DATAFRAME

Question:
Hi

Answer:
CHAT

Return ONLY ONE WORD.

SQL
RAG
BOTH
DATAFRAME
CHAT

"""

        response = router.planner().invoke(prompt)

        print("\n========== RAW NEMOTRON ==========")
        print(response.content)

        text = response.content.upper()

        print("\n========== PARSED ==========")
        print(text)

        if "DATAFRAME" in text:
            intent = "DATAFRAME"
        elif "BOTH" in text:
            intent = "BOTH"
        elif "SQL" in text:
            intent = "SQL"
        elif "RAG" in text:
            intent = "RAG"
        elif "CHAT" in text:
            intent = "CHAT"
        else:
            intent = "CHAT"
        print("\n========== FINAL INTENT ==========")
        print(intent)
        validation = self.validator.validate(question, intent)

        if validation["decision"] == "FAIL":
            intent = "CHAT"

        log("PLANNER", f"Intent = {intent}")
        return intent
