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
        # WORKSPACE (GMAIL / SHEETS)
        # -----------------------------
        workspace_patterns = [
            "email",
            "emails",
            "gmail",
            "inbox",
            "unread",
            "google sheet",
            "google sheets",
            "spreadsheet",
        ]
        if any(x in q for x in workspace_patterns):
            return "WORKSPACE"

        # -----------------------------
        # CHAT (Exact match greetings only)
        # -----------------------------
        if re.fullmatch(
            r"(hi|hello|hey|thanks|thank you|bye|goodbye|good morning|good evening)",
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
        # COMPREHENSIVE LOGISTICS RAG PATTERNS
        # -----------------------------
        rag_patterns = [
            # Document Type Identifiers
            "sop",
            "policy",
            "documentation",
            "document",
            "manual",
            "guideline",
            "guidelines",
            "procedure",
            "process",
            "rule",
            "rules",
            "escalation",
            "clause",
            "terms",
            "requirement",
            "requirements",
            # Returns & Deliveries (RVP, RTO, DTO, Doorstep)
            "rvp",
            "rto",
            "dto",
            "forward delivery",
            "return leg",
            "reverse",
            "reverse pickup",
            "doorstep",
            "door step",
            "seller doorstep",
            "pickup",
            "delivery",
            "handover",
            "non-qc",
            "qc shipment",
            # Proofs, Evidence & Footage
            "pod",
            "proof of delivery",
            "unboxing",
            "packing video",
            "unpacking video",
            "footage",
            "timestamp",
            "time stamp",
            "image",
            "images",
            "picture",
            "photo",
            "evidence",
            "remark",
            "remarks",
            # Claims & Incidents
            "dispute",
            "damage",
            "damaged",
            "tampered",
            "partial delivery",
            "empty parcel",
            "wrong product",
            "shortage",
            "shorter image",
            "claim",
            "investigate",
            "tat",
            "timeline",
            "re-validation",
            # Stakeholders & Operations
            "fe",
            "field executive",
            "kam",
            "key account manager",
            "savex",
            "delhivery",
            "shiprocket",
            "warehouse",
            "client part",
        ]

        # -----------------------------
        # SQL PATTERNS
        # -----------------------------
        # Replace broad keywords with specific analytical phrases:
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
            "database",
            "sql",
            "count of shipments",
            "number of shipments",
            "list shipments",
            "show shipments",
        ]

        has_rag = any(x in q for x in rag_patterns)
        has_sql = any(x in q for x in sql_patterns)

        # -----------------------------
        # INTENT EVALUATION
        # -----------------------------
        if has_rag and has_sql:
            return "BOTH"

        if has_sql:
            return "SQL"

        if has_rag:
            return "RAG"

        # Unknown → Remote Planner (NVIDIA)
        return None

    # ============================================================
    # PLAN CREATION
    # ============================================================

    def create_plan(self, question):
        local_intent = self.local_intent(question)

        if local_intent:
            print(f"[HYBRID PLANNER] Local intent = {local_intent}")
            intent = local_intent
        else:
            print("[HYBRID PLANNER] Ambiguous question → NVIDIA Planner")
            context = self.memory.get_context()
            intent = self.planner.plan(question, context)

        self.memory.add_user(question)

        if intent == "WORKSPACE":
            return {"intent": "WORKSPACE", "tools": ["workspace"]}
        if intent == "SQL":
            return {"intent": "SQL", "tools": ["sql"]}
        if intent == "RAG":
            return {"intent": "RAG", "tools": ["rag"]}
        if intent == "BOTH":
            return {"intent": "BOTH", "tools": ["sql", "rag"]}
        if intent == "DATAFRAME":
            return {"intent": "DATAFRAME", "tools": ["dataframe"]}

        return {
            "intent": "CHAT",
            "tools": [],
        }
