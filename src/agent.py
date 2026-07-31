from src.planner_engine import PlannerEngine
from src.logger import log
from src.supervisor.supervisor import Supervisor
from src.question_normalizer import QuestionNormalizer
from src.text_normalizer import normalize
import time
from src.quality.checker import QualityChecker


class DelhiveryAgent:

    def __init__(self):

        self.planner = PlannerEngine()
        self.supervisor = Supervisor()
        self.normalizer = QuestionNormalizer()
        self.quality = QualityChecker()

        log("AGENT", "Ready")

    def ask(self, question):

        # -----------------------------
        # Save User Message
        # -----------------------------
        self.planner.memory.add_user(question)

        start = time.time()

        plan = self.planner.create_plan(question)

        print(f"Planner: {time.time()-start:.2f}s")

        intent = plan["intent"]

        log("PLANNER", f"Intent = {intent}")

        # =====================================================
        # SQL
        # =====================================================

        if intent == "SQL":

            log("AGENT", "Calling SQL Tool")

            normalized_question = normalize(question)

            print("ORIGINAL SQL QUESTION :", question)
            print("NORMALIZED SQL QUESTION :", normalized_question)

            tool_result = self.supervisor.sql(normalized_question)

            if isinstance(tool_result, dict) and tool_result.get("type") == "error":
                return {
                    "answer": tool_result["message"],
                    "tool_result": tool_result,
                }

            self.planner.memory.add_ai(tool_result["answer"])

            return {
                "answer": tool_result["answer"],
                "tool_result": tool_result,
            }

        # =====================================================
        # RAG
        # =====================================================

        elif intent == "RAG":

            log("AGENT", "Calling RAG Tool")

            rag_answer = self.supervisor.rag_search(question)

            self.planner.memory.add_ai(rag_answer)

            return {
                "answer": rag_answer,
                "tool_result": None,
            }

        # =====================================================
        # BOTH
        # =====================================================

        elif intent == "BOTH":

            log("AGENT", "Calling SQL + RAG")

            parts = self.normalizer.split(question)

            sql_question = parts.get("sql", question)
            rag_question = parts.get("rag", question)

            print("\nSQL QUESTION :", sql_question)
            print("RAG QUESTION :", rag_question)

            sql_result = self.supervisor.sql(sql_question)

            if isinstance(sql_result, dict) and sql_result.get("type") == "error":

                return {
                    "answer": sql_result.get("message", "SQL failed."),
                    "tool_result": sql_result,
                }

            rag_result = self.supervisor.rag_search(rag_question)

            sql_answer = sql_result.get("answer")

            if not sql_answer:
                sql_answer = sql_result.get("message", "SQL result not available.")

            answer = f"""{sql_answer}

--------------------------------------

📄 Additional Information

{rag_result}
"""

            self.planner.memory.add_ai(answer)

            return {
                "answer": answer,
                "tool_result": sql_result,
            }

        # =====================================================
        # DATAFRAME
        # =====================================================

        elif intent == "DATAFRAME":

            log("AGENT", "Calling DataFrame Agent")

            result = self.supervisor.dataframe(question)

            if result is None:

                return {
                    "answer": "No SQL result found. Run a SQL query first.",
                    "tool_result": None,
                }

            self.planner.memory.add_ai(result["answer"])

            return {
                "answer": result["answer"],
                "tool_result": {
                    "type": "table",
                    "columns": list(result["dataframe"].columns),
                    "rows": result["dataframe"].values.tolist(),
                    "sql": "",
                    "time": 0,
                    "answer": result["answer"],
                },
            }

        # =====================================================
        # CHAT
        # =====================================================

        else:

            log("AGENT", "Calling Chat Model")

            context = self.planner.memory.get_context()

            prompt = f"""
            You are Delhivery AI Assistant.

            Conversation History:
           {context}

            Current User Message:
            {question}

            Instructions:
           - Reply naturally.
           - Remember previous conversation.
           - Answer using Conversation History whenever possible.
           - Be concise.
            """

            answer = self.supervisor.chat(prompt)

            self.planner.memory.add_ai(answer)

            return {
                "answer": answer,
                "tool_result": None,
            }
