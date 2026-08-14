from src.models.router import ModelRouter
from src.planner_validator import PlannerValidator
from src.router.smart_router import SmartRouter
from src.logger import log


router = ModelRouter()


class Planner:

    def __init__(self):
        self.validator = PlannerValidator()
        self.smart_router = SmartRouter()
        self.last_route = None

    def plan(self, question, context=""):

        route_result = self.smart_router.route(question)
        self.last_route = dict(route_result)

        if route_result["intent"] is not None:
            intent = route_result["intent"]

            validation = self.validator.validate(question, intent)

            if validation["decision"] == "FAIL":
                log("PLANNER", f"Invalid routed intent detected: {intent}")
                intent = "CHAT"

            self.last_route["intent"] = intent
            log(
                "PLANNER",
                f"intent={intent} method={self.last_route['method']} "
                f"score={self.last_route['score']} "
                f"memory={self.last_route['memory']}",
            )
            return intent

        prompt = f"""
You are the Intent Planner for a Delhivery Logistics Agent.

Your job is ONLY to classify the user's request into exactly ONE intent.

AVAILABLE INTENTS:

SQL
Use SQL when the user asks about:
- shipment counts
- AWB
- tracking
- warehouse/DC data
- shipment data
- customers
- database information
- sums
- averages
- minimum
- maximum
- filtering database records
- grouping database records
- sorting database records
- dates in database records

RAG
Use RAG when the user asks about:
- SOP
- policy
- documentation
- process
- manual
- guidelines
- company instructions

BOTH
Use BOTH when the user needs:
- database information AND documentation/SOP/policy information

DATAFRAME
Use DATAFRAME ONLY when the user refers to an EXISTING SQL RESULT.

Examples:
- Sort this
- Filter this
- Top 10 from this result
- Plot this
- Average of this result
- Show only delayed shipments from this result
- Group this result

CHAT
Use CHAT for:
- Hello
- Hi
- Greetings
- Thanks
- Bye
- General conversation

IMPORTANT RULES:

1. Return exactly ONE word.
2. The word MUST be one of:

SQL
RAG
BOTH
DATAFRAME
CHAT

3. Never return explanations.
4. Never return punctuation.
5. Never return JSON.
6. Never return markdown.
7. If the user asks for database information, choose SQL.
8. If the user asks for SOP/policy/process information, choose RAG.
9. If both database information and documentation are required, choose BOTH.
10. Choose DATAFRAME only when an existing SQL result is explicitly referenced.

Examples:

User:
How many shipments are there?

SQL

User:
Show total AWB by warehouse.

SQL

User:
What is the average shipment weight?

SQL

User:
Explain the closure process.

RAG

User:
What is the SOP for lost shipments?

RAG

User:
Show total AWB by warehouse and explain the closure process.

BOTH

User:
Sort this result by weight.

DATAFRAME

User:
Show the top 10 from this result.

DATAFRAME

User:
Hi

CHAT

Conversation:
{context}

User Question:
{question}

Return ONLY ONE WORD.
"""

        response = router.planner().invoke(prompt)

        raw_output = response.content.strip()

        print("\n========== RAW NEMOTRON ==========")
        print(raw_output)

        text = raw_output.upper().strip()

        print("\n========== PARSED ==========")
        print(text)

        # -------------------------------------------------
        # Strict intent extraction
        # -------------------------------------------------

        valid_intents = {
            "SQL",
            "RAG",
            "BOTH",
            "DATAFRAME",
            "CHAT",
        }

        # Exact match first
        if text in valid_intents:
            intent = text

        else:
            # Fallback for unexpected model formatting
            intent = "CHAT"

            for candidate in (
                "DATAFRAME",
                "BOTH",
                "SQL",
                "RAG",
                "CHAT",
            ):
                if candidate in text:
                    intent = candidate
                    break

        print("\n========== FINAL INTENT ==========")
        print(intent)

        # -------------------------------------------------
        # Validate planner decision
        # -------------------------------------------------

        validation = self.validator.validate(
            question,
            intent
        )

        print("\n========== PLANNER VALIDATION ==========")
        print(validation)

        if validation["decision"] == "FAIL":

            log(
                "PLANNER",
                f"Invalid intent detected: {intent}"
            )

            intent = "CHAT"

        else:

            self.smart_router.save_nemotron_decision(question, intent)

        self.last_route.update(
            {
                "intent": intent,
                "method": "NEMOTRON",
            }
        )

        log(
            "PLANNER",
            f"intent={intent} method=NEMOTRON "
            f"score={self.last_route['score']} "
            f"memory={self.last_route['memory']}",
        )

        return intent
