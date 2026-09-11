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
    # LOCAL FALLBACK (Only used if LLM fails)
    # ============================================================
    def local_fallback(self, question: str) -> str:
        q = question.lower().strip()

        if re.fullmatch(r"(hi|hello|hey|thanks|thank you|bye|goodbye)", q):
            return "CHAT"

        dataframe_patterns = ["sort this", "filter this", "top 10", "plot this", "average of this", "show only", "group this"]
        if any(pattern in q for pattern in dataframe_patterns):
            return "DATAFRAME"

        sql_terms = ["count", "how many", "total", "sum", "average", "avg", "max", "min", "shipment", "shipments", "awb", "tracking", "warehouse", "database"]
        rag_patterns = ["sop", "policy", "documentation", "process", "manual", "guideline", "guidelines", "procedure", "explain closure process"]

        has_sql = any(term in q for term in sql_terms)
        has_rag = any(term in q for term in rag_patterns)

        if has_sql and has_rag:
            return "BOTH"
        if has_sql:
            return "SQL"
        if has_rag:
            return "RAG"
        
        # We must return None here, NOT "CHAT", so the hybrid planner knows it failed to guess.
        return None 

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
                print(f"[PLANNER] Remote planner attempt {attempt}/{max_retries} failed: {error_text}")
                if attempt < max_retries:
                    delay = 1.5 * attempt
                    print(f"[PLANNER] Retrying in {delay:.1f}s...")
                    time.sleep(delay)
        return None

    # ============================================================
    # MAIN PLAN
    # ============================================================
    def plan(self, question, context=""):

        # 1. INTELLIGENT LLM ROUTING (Primary)
        print("[HYBRID PLANNER] Sending to NVIDIA Planner...")
        prompt = f"""
You are an intelligent Intent Classifier for a Logistics API.
Analyze the user's question and choose EXACTLY ONE of the following routing labels:

- RAG: The user is asking about operational rules, policies, SOPs, guidelines, requirements, SLAs, or factual information that would be found in a PDF manual or training document (e.g., "What are the rules for...", "How do I process...", "What is the requirement for...").
- SQL: The user is asking for specific quantitative data, counts, or metrics from a live tracking database (e.g., "How many shipments...", "What is the status of AWB...").
- BOTH: The question requires BOTH live database metrics AND checking a policy document.
- DATAFRAME: The user is asking to sort, filter, or graph data that is already on the screen.
- CHAT: The user is just saying hello, thank you, or having a casual conversation.

Conversation History:
{context}

User Question:
{question}

Return ONLY ONE WORD (RAG, SQL, BOTH, DATAFRAME, or CHAT). No explanations.
"""
        text = self._remote_plan(prompt)

        # 2. PARSE LLM RESPONSE
        intent = None
        if text is not None:
            print("\n========== RAW NEMOTRON ==========")
            print(text)
            text = text.upper().strip()

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

        # 3. FALLBACK TO LOCAL KEYWORDS (Only if LLM failed or returned garbage)
        if intent is None:
            print("\n[PLANNER] Remote planner unavailable or invalid. Using local fallback.")
            intent = self.local_fallback(question) or "CHAT" 

        # 4. VALIDATION
        validation = self.validator.validate(question, intent)
        if validation["decision"] == "FAIL":
            print(f"[PLANNER] Validation failed: {validation.get('reason')}")
            intent = self.local_fallback(question) or "CHAT"

        print("\n========== FINAL INTENT ==========")
        print(intent)
        log("PLANNER", f"Intent = {intent}")

        return intent