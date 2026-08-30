import time

from src.logger import log


class AgentOrchestrator:
    """
    Sprint 6 multi-agent execution layer.

    Routes an already-classified plan to the appropriate
    specialist agents and returns a unified result.
    """

    def __init__(self, supervisor):
        self.supervisor = supervisor

        log(
            "ORCHESTRATOR",
            "Multi-agent orchestrator ready",
        )

    # ============================================================
    # EXECUTE PLAN
    # ============================================================

    def execute(self, plan, question, normalizer=None):

        start = time.time()

        intent = plan.get("intent", "CHAT")
        tools = plan.get("tools", [])

        log(
            "ORCHESTRATOR",
            f"Intent={intent} Tools={tools}",
        )

        # --------------------------------------------------------
        # SQL
        # --------------------------------------------------------

        if intent == "SQL":

            result = self.supervisor.sql(question)

            return self._finish(
                intent,
                result,
                start,
            )

        # --------------------------------------------------------
        # RAG
        # --------------------------------------------------------

        if intent == "RAG":

            result = self.supervisor.rag_search(question)

            return self._finish(
                intent,
                {
                    "type": "rag",
                    "answer": result,
                },
                start,
            )

        # --------------------------------------------------------
        # BOTH
        # --------------------------------------------------------

        if intent == "BOTH":

            if normalizer is not None:
                parts = normalizer.split(question)
            else:
                parts = {
                    "sql": question,
                    "rag": question,
                }

            sql_question = parts.get(
                "sql",
                question,
            )

            rag_question = parts.get(
                "rag",
                question,
            )

            sql_result = self.supervisor.sql(sql_question)

            if isinstance(sql_result, dict) and sql_result.get("type") == "error":

                return self._finish(
                    intent,
                    sql_result,
                    start,
                )

            rag_result = self.supervisor.rag_search(rag_question)

            sql_answer = sql_result.get(
                "answer",
                "SQL result unavailable.",
            )

            answer = (
                f"{sql_answer}\n\n"
                "--------------------------------------\n\n"
                "Additional Information\n\n"
                f"{rag_result}"
            )

            return self._finish(
                intent,
                {
                    "type": "both",
                    "answer": answer,
                    "sql_result": sql_result,
                    "rag_result": rag_result,
                },
                start,
            )

        # --------------------------------------------------------
        # DATAFRAME
        # --------------------------------------------------------

        if intent == "DATAFRAME":

            result = self.supervisor.dataframe(question)

            if result is None:

                return self._finish(
                    intent,
                    {
                        "type": "error",
                        "message": ("No SQL result found. " "Run a SQL query first."),
                    },
                    start,
                )

            tool_result = {
                "type": "table",
                "columns": list(result["dataframe"].columns),
                "rows": result["dataframe"].values.tolist(),
                "sql": "",
                "time": 0,
                "answer": result["answer"],
            }

            return self._finish(
                intent,
                {
                    "type": "dataframe",
                    "answer": result["answer"],
                    "tool_result": tool_result,
                },
                start,
            )

        # --------------------------------------------------------
        # CHAT
        # --------------------------------------------------------

        context = (
            self.supervisor.chat_memory_context()
            if hasattr(
                self.supervisor,
                "chat_memory_context",
            )
            else ""
        )

        prompt = f"""
You are Delhivery AI Assistant.

Conversation History:
{context}

Current User Message:
{question}

Reply naturally and concisely.
"""

        answer = self.supervisor.chat(prompt)

        return self._finish(
            "CHAT",
            {
                "type": "chat",
                "answer": answer,
            },
            start,
        )

    # ============================================================
    # RESULT NORMALIZATION
    # ============================================================

    @staticmethod
    def _finish(
        intent,
        result,
        start,
    ):

        elapsed = round(
            time.time() - start,
            4,
        )

        log(
            "ORCHESTRATOR",
            f"{intent} completed in {elapsed}s",
        )

        # ============================================================
        # AGENT ERROR
        # ============================================================

        if isinstance(result, dict) and result.get("type") == "error":

            return {
                "intent": intent,
                "answer": result.get(
                    "message",
                    "Agent execution failed.",
                ),
                "tool_result": result,
                "execution_time": elapsed,
            }

        # ============================================================
        # SQL RESULT
        # ============================================================

        if intent == "SQL" and isinstance(result, dict):

            # Keep complete SQL result internally,
            # but don't send hundreds/thousands of rows
            # through the API response.

            MAX_RESPONSE_ROWS = 20

            tool_result = result.copy()

            rows = tool_result.get(
                "rows",
                [],
            )

            if isinstance(rows, list):

                tool_result["total_rows"] = len(rows)

                tool_result["rows"] = rows[:MAX_RESPONSE_ROWS]

                tool_result["truncated"] = len(rows) > MAX_RESPONSE_ROWS

            return {
                "intent": intent,
                "answer": result.get(
                    "answer",
                    "",
                ),
                "tool_result": tool_result,
                "execution_time": elapsed,
            }

        # ============================================================
        # RAG / CHAT / DATAFRAME
        # ============================================================

        if isinstance(result, dict):

            return {
                "intent": intent,
                "answer": result.get(
                    "answer",
                    "",
                ),
                "tool_result": result,
                "execution_time": elapsed,
            }

        # ============================================================
        # PLAIN STRING
        # ============================================================

        return {
            "intent": intent,
            "answer": str(result),
            "tool_result": None,
            "execution_time": elapsed,
        }
