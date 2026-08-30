import re

from src.planner import Planner
from src.memory.chat_memory import ChatMemory


class PlannerEngine:

    def __init__(self):
        self.planner = Planner()
        self.memory = ChatMemory()

    # ============================================================
    # FAST LOCAL ROUTER
    # ============================================================

    def local_intent(self, question: str):
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
            "group this",
            "show only",
            "average of this",
        ]

        if any(x in q for x in dataframe_patterns):
            return "DATAFRAME"

        # -----------------------------
        # RAG
        # -----------------------------

        rag_patterns = [
            "sop",
            "policy",
            "documentation",
            "document",
            "manual",
            "guideline",
            "guidelines",
            "procedure",
            "process",
            "explain",
        ]

        # Strong SQL indicators
        sql_patterns = [
            "how many",
            "count",
            "total",
            "sum",
            "average",
            "avg",
            "maximum",
            "minimum",
            "max",
            "min",
            "shipment",
            "shipments",
            "awb",
            "tracking",
            "warehouse",
            "database",
            "status",
        ]

        has_rag = any(x in q for x in rag_patterns)
        has_sql = any(x in q for x in sql_patterns)

        # -----------------------------
        # BOTH
        # -----------------------------

        if has_rag and has_sql:
            return "BOTH"

        # -----------------------------
        # SQL
        # -----------------------------

        if has_sql:
            return "SQL"

        # -----------------------------
        # RAG
        # -----------------------------

        if has_rag:
            return "RAG"

        # Unknown → remote planner
        return None

    # ============================================================
    # PLAN
    # ============================================================

    def create_plan(self, question):

        # --------------------------------------------------------
        # 1. FAST LOCAL ROUTING
        # --------------------------------------------------------

        local_intent = self.local_intent(question)

        if local_intent:

            print(
                f"[HYBRID PLANNER] Local intent = "
                f"{local_intent}"
            )

            intent = local_intent

        # --------------------------------------------------------
        # 2. REMOTE PLANNER FOR AMBIGUOUS QUESTIONS
        # --------------------------------------------------------

        else:

            print(
                "[HYBRID PLANNER] Ambiguous question → "
                "NVIDIA Planner"
            )

            context = self.memory.get_context()

            intent = self.planner.plan(
                question,
                context,
            )

        # --------------------------------------------------------
        # 3. MEMORY
        # --------------------------------------------------------

        self.memory.add_user(question)

        # --------------------------------------------------------
        # 4. TOOL PLAN
        # --------------------------------------------------------

        if intent == "SQL":

            return {
                "intent": "SQL",
                "tools": ["sql"],
            }

        if intent == "RAG":

            return {
                "intent": "RAG",
                "tools": ["rag"],
            }

        if intent == "BOTH":

            return {
                "intent": "BOTH",
                "tools": ["sql", "rag"],
            }

        if intent == "DATAFRAME":

            return {
                "intent": "DATAFRAME",
                "tools": ["dataframe"],
            }

        return {
            "intent": "CHAT",
            "tools": [],
        }