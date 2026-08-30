import re
import time

from src.models.router import ModelRouter
from src.planner_validator import PlannerValidator
from src.logger import log


router = ModelRouter()


class Planner:

    def __init__(self):
        self.validator = PlannerValidator()

    # ============================================================
    # LOCAL FALLBACK
    # ============================================================

    def local_fallback(self, question: str) -> str:

        q = question.lower().strip()

        # -----------------------------
        # CHAT
        # -----------------------------

        if re.fullmatch(
            r"(hi|hello|hey|thanks|thank you|bye|goodbye)",
            q,
        ):
            return "CHAT"

        # -----------------------------
        # DATAFRAME
        # -----------------------------

        dataframe_patterns = [
            "sort this",
            "filter this",
            "top 10",
            "plot this",
            "average of this",
            "show only",
            "group this",
        ]

        if any(pattern in q for pattern in dataframe_patterns):
            return "DATAFRAME"

        # -----------------------------
        # RAG
        # -----------------------------

        rag_patterns = [
            "sop",
            "policy",
            "documentation",
            "process",
            "manual",
            "guideline",
            "guidelines",
            "procedure",
            "explain closure process",
        ]

        if any(pattern in q for pattern in rag_patterns):
            return "RAG"

        # -----------------------------
        # BOTH
        # -----------------------------

        sql_terms = [
            "count",
            "how many",
            "total",
            "sum",
            "average",
            "avg",
            "max",
            "min",
            "shipment",
            "shipments",
            "awb",
            "tracking",
            "warehouse",
            "database",
        ]

        has_sql = any(term in q for term in sql_terms)
        has_rag = any(term in q for term in rag_patterns)

        if has_sql and has_rag:
            return "BOTH"

        # -----------------------------
        # SQL
        # -----------------------------

        if has_sql:
            return "SQL"

        return "CHAT"

    # ============================================================
    # NVIDIA PLANNER
    # ============================================================

    def _remote_plan(self, prompt: str):

        max_retries = 3

        for attempt in range(1, max_retries + 1):

            try:

                response = router.planner().invoke(prompt)

                return response.content

            except Exception as exc:

                error_text = str(exc)

                print(
                    f"[PLANNER] Remote planner attempt "
                    f"{attempt}/{max_retries} failed: {error_text}"
                )

                # Retry only service-overload / temporary failures
                if "503" not in error_text and "Service temporarily overloaded" not in error_text:
                    raise

                if attempt < max_retries:

                    delay = 1.5 * attempt

                    print(
                        f"[PLANNER] Retrying in {delay:.1f}s..."
                    )

                    time.sleep(delay)

        return None

    # ============================================================
    # MAIN PLAN
    # ============================================================

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

        # ========================================================
        # REMOTE PLANNER
        # ========================================================

        text = self._remote_plan(prompt)

        if text is not None:

            print("\n========== RAW NEMOTRON ==========")
            print(text)

            text = text.upper().strip()

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
                intent = self.local_fallback(question)

        # ========================================================
        # LOCAL FALLBACK
        # ========================================================

        else:

            print(
                "\n[PLANNER] Remote planner unavailable."
            )

            intent = self.local_fallback(question)

            print(
                f"[PLANNER] Local fallback intent = {intent}"
            )

        # ========================================================
        # VALIDATION
        # ========================================================

        validation = self.validator.validate(
            question,
            intent,
        )

        if validation["decision"] == "FAIL":

            print(
                f"[PLANNER] Validation failed: "
                f"{validation.get('reason', 'Unknown reason')}"
            )

            intent = self.local_fallback(question)

        print("\n========== FINAL INTENT ==========")
        print(intent)

        log(
            "PLANNER",
            f"Intent = {intent}",
        )

        return intent