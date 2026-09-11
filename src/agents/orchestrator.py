import time
import uuid
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import (
    MemorySaver,
)  # <-- NEW: Built-in SQLite/In-Memory state tracker

from src.logger import log


class AgentState(TypedDict):
    question: str
    intent: str
    tools: list
    sql_result: Optional[dict]
    rag_result: Optional[str]
    df_result: Optional[dict]
    answer: str
    error: Optional[str]


class AgentOrchestrator:
    def __init__(self, supervisor):
        self.supervisor = supervisor

        workflow = StateGraph(AgentState)

        workflow.add_node("sql_agent", self.node_sql)
        workflow.add_node("rag_agent", self.node_rag)
        workflow.add_node("both_agent", self.node_both)
        workflow.add_node("dataframe_agent", self.node_dataframe)
        workflow.add_node("workspace_agent", self.node_workspace)
        workflow.add_node("chat_agent", self.node_chat)

        workflow.set_conditional_entry_point(
            self.route_intent,
            {
                "SQL": "sql_agent",
                "RAG": "rag_agent",
                "BOTH": "both_agent",
                "DATAFRAME": "dataframe_agent",
                "WORKSPACE": "workspace_agent",
                "CHAT": "chat_agent",
            },
        )

        workflow.add_edge("sql_agent", END)
        workflow.add_edge("rag_agent", END)
        workflow.add_edge("both_agent", END)
        workflow.add_edge("dataframe_agent", END)
        workflow.add_edge("workspace_agent", END)
        workflow.add_edge("chat_agent", END)

        # NEW: Initialize the memory saver
        self.memory = MemorySaver()

        # NEW: Compile the graph WITH memory checking
        self.app = workflow.compile(checkpointer=self.memory)
        log("ORCHESTRATOR", "LangGraph orchestrator ready with MemorySaver")

    # ============================================================
    # VISUALIZATION (See it like n8n)
    # ============================================================

    # ============================================================
    # VISUALIZATION
    # ============================================================
    def get_workflow_image(self):
        """Returns the raw PNG bytes or Mermaid text safely."""
        try:
            return self.app.get_graph().draw_mermaid_png()
        except Exception as e:
            log("ORCHESTRATOR", f"PNG generation unavailable, falling back: {e}")
            return None

    def get_workflow_mermaid(self):
        """Returns raw Mermaid diagram text (100% crash-proof)."""
        try:
            return self.app.get_graph().draw_mermaid()
        except Exception:
            return None

    # ============================================================
    # ROUTER
    # ============================================================
    def route_intent(self, state: AgentState):
        """Reads the intent from the state and tells the graph which node to fire."""
        return state["intent"]

    # ============================================================
    # NODES (Agent Logic)
    # ============================================================
    def node_sql(self, state: AgentState):
        result = self.supervisor.sql(state["question"])
        if isinstance(result, dict) and result.get("type") == "error":
            return {"error": result.get("message"), "answer": result.get("message")}
        return {"sql_result": result, "answer": result.get("answer", "")}

    def node_rag(self, state: AgentState):
        raw_result = self.supervisor.rag_search(state["question"])

        # Safely extract the text answer if RAG returns a LangChain dictionary
        answer_text = ""
        if isinstance(raw_result, dict):
            answer_text = (
                raw_result.get("answer") or raw_result.get("result") or str(raw_result)
            )
        else:
            answer_text = str(raw_result)

        return {"rag_result": raw_result, "answer": answer_text}

    def node_both(self, state: AgentState):
        sql_res = self.supervisor.sql(state["question"])
        rag_res = self.supervisor.rag_search(state["question"])

        sql_text = (
            sql_res.get("answer", "SQL result unavailable.")
            if isinstance(sql_res, dict)
            else str(sql_res)
        )

        rag_text = ""
        if isinstance(rag_res, dict):
            rag_text = rag_res.get("answer") or rag_res.get("result") or str(rag_res)
        else:
            rag_text = str(rag_res)

        answer = f"{sql_text}\n\n--------------------------------------\n\nAdditional SOP Info:\n{rag_text}"

        return {"sql_result": sql_res, "rag_result": rag_res, "answer": answer}

    def node_dataframe(self, state: AgentState):
        result = self.supervisor.dataframe(state["question"])
        if not result or result.get("type") == "error":
            msg = "No SQL result found. Run a SQL query first."
            return {"error": msg, "answer": msg}
        return {"df_result": result, "answer": result.get("answer", "")}

    def node_chat(self, state: AgentState):
        context = (
            self.supervisor.chat_memory_context()
            if hasattr(self.supervisor, "chat_memory_context")
            else ""
        )
        prompt = f"Conversation History:\n{context}\n\nUser Message:\n{state['question']}\n\nReply naturally."
        answer = self.supervisor.chat(prompt)
        return {"answer": answer}

    # ============================================================
    # MAIN EXECUTION ENTRY POINT
    # ============================================================
    # ============================================================
    # MAIN EXECUTION ENTRY POINT
    # ============================================================
    # ============================================================
    # MAIN EXECUTION ENTRY POINT
    # ============================================================
    def execute(self, plan, question, normalizer=None, thread_id="default_user"):
        start = time.time()
        intent = plan.get("intent", "CHAT")

        config = {"configurable": {"thread_id": thread_id}}

        input_state = {
            "question": question,
            "intent": intent,
            "tools": plan.get("tools", []),
        }

        final_state = self.app.invoke(input_state, config=config)
        elapsed = round(time.time() - start, 4)

        # Ensure tool_result is NEVER None regardless of intent
        tool_result = {}

        if intent == "SQL":
            tool_result = final_state.get("sql_result") or {}
            if isinstance(tool_result, dict) and "rows" in tool_result:
                tool_result["total_rows"] = len(tool_result["rows"])
                tool_result["rows"] = tool_result["rows"][:20]
                tool_result["truncated"] = tool_result["total_rows"] > 20

        elif intent == "DATAFRAME":
            tool_result = final_state.get("df_result") or {}

        elif intent == "RAG":
            tool_result = {
                "type": "rag",
                "rag_result": final_state.get("rag_result", ""),
            }

        elif intent == "WORKSPACE":
            tool_result = {"type": "workspace"}

        elif intent == "BOTH":
            tool_result = {
                "type": "both",
                "sql_result": final_state.get("sql_result"),
                "rag_result": final_state.get("rag_result"),
            }

        else:
            tool_result = {"type": "chat"}

        return {
            "intent": intent,
            "answer": final_state.get("answer", "Agent execution failed."),
            "tool_result": tool_result,
            "execution_time": elapsed,
        }

    # ============================================================
    # NODES (Agent Logic)
    # ============================================================
    def node_sql(self, state: AgentState):
        result = self.supervisor.sql(state["question"])
        if isinstance(result, dict):
            if result.get("type") == "error":
                return {
                    "error": result.get("message"),
                    "answer": result.get("message", "SQL execution error."),
                }
            ans = result.get("answer") or str(result)
        else:
            ans = str(result or "No SQL result generated.")
        return {"sql_result": result, "answer": ans}

    def node_rag(self, state: AgentState):
        result = self.supervisor.rag_search(state["question"])

        # Default to dumping the raw data to the screen so it's never empty
        ans = str(result)

        # Attempt to cleanly extract the text if it's a dictionary
        if isinstance(result, dict):
            # Check all common keys AI frameworks use
            for key in [
                "answer",
                "result",
                "response",
                "output",
                "content",
                "documents",
            ]:
                if key in result and result[key]:
                    ans = str(result[key])
                    break
        elif isinstance(result, str) and result.strip():
            ans = result

        if not ans or ans == "{}":
            ans = "No SOP or policy document found for your request."

        return {"rag_result": result, "answer": ans}

    def node_both(self, state: AgentState):
        sql_res = self.supervisor.sql(state["question"])
        rag_res = self.supervisor.rag_search(state["question"])

        sql_ans = (
            sql_res.get("answer", "")
            if isinstance(sql_res, dict)
            else str(sql_res or "")
        )
        if isinstance(rag_res, dict):
            rag_ans = rag_res.get("answer", "")
        else:
            rag_ans = str(rag_res or "")

        combined_ans = f"{sql_ans}\n\n--------------------------------------\n\nAdditional SOP Info:\n{rag_ans}".strip()
        if not combined_ans:
            combined_ans = "No response generated."
        return {"sql_result": sql_res, "rag_result": rag_res, "answer": combined_ans}

    def node_dataframe(self, state: AgentState):
        result = self.supervisor.dataframe(state["question"])
        if not result or (isinstance(result, dict) and result.get("type") == "error"):
            msg = (
                result.get(
                    "message", "No SQL result found in memory. Run a SQL query first."
                )
                if isinstance(result, dict)
                else "Dataframe analysis failed."
            )
            return {"error": msg, "answer": msg}
        ans = result.get("answer") if isinstance(result, dict) else str(result)
        return {"df_result": result, "answer": ans or "DataFrame analysis complete."}

    def node_workspace(self, state: AgentState):
        q = state["question"].lower()
        if "sheet" in q:
            result = self.supervisor.workspace(action="read_sheet", query=q)
        else:
            result = self.supervisor.workspace(action="read_emails", query="is:unread")

        if isinstance(result, dict) and result.get("status") == "error":
            msg = f"Workspace Error: {result.get('message')}"
            return {"error": msg, "answer": msg}

        data = result.get("data", []) if isinstance(result, dict) else []
        if not data:
            answer = "No emails or spreadsheet records found."
        elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            email_summary = []
            for item in data[:5]:
                email_summary.append(
                    f"• **{item.get('subject')}** from {item.get('from')}\n  _{item.get('snippet')}_"
                )
            answer = "Here are your latest emails:\n\n" + "\n\n".join(email_summary)
        else:
            answer = f"Retrieved workspace data successfully: {data}"

        return {"answer": answer}

    def node_chat(self, state: AgentState):
        context = (
            self.supervisor.chat_memory_context()
            if hasattr(self.supervisor, "chat_memory_context")
            else ""
        )
        prompt = f"Conversation History:\n{context}\n\nUser Message:\n{state['question']}\n\nReply naturally."
        answer = self.supervisor.chat(prompt)
        return {"answer": str(answer or "No chat response generated.")}

    # ============================================================
    # MAIN EXECUTION ENTRY POINT
    # ============================================================
    def execute(self, plan, question, normalizer=None, thread_id="default_user"):
        start = time.time()
        intent = plan.get("intent", "CHAT")

        config = {"configurable": {"thread_id": thread_id}}
        input_state = {
            "question": question,
            "intent": intent,
            "tools": plan.get("tools", []),
        }

        final_state = self.app.invoke(input_state, config=config)
        elapsed = round(time.time() - start, 4)

        tool_result = {}
        if intent == "SQL":
            tool_result = final_state.get("sql_result") or {}
            if isinstance(tool_result, dict) and "rows" in tool_result:
                tool_result["total_rows"] = len(tool_result["rows"])
                tool_result["rows"] = tool_result["rows"][:20]
                tool_result["truncated"] = tool_result["total_rows"] > 20

        elif intent == "DATAFRAME":
            tool_result = final_state.get("df_result") or {}

        elif intent == "RAG":
            tool_result = {
                "type": "rag",
                "rag_result": final_state.get("rag_result", {}),
            }

        elif intent == "WORKSPACE":
            tool_result = {"type": "workspace"}

        elif intent == "BOTH":
            tool_result = {
                "type": "both",
                "sql_result": final_state.get("sql_result"),
                "rag_result": final_state.get("rag_result"),
            }
        else:
            tool_result = {"type": "chat"}

        # Extract clean answer string safely
        ans_text = final_state.get("answer")
        if isinstance(ans_text, dict):
            ans_text = ans_text.get("answer") or ans_text.get("result") or str(ans_text)
        elif not ans_text or not str(ans_text).strip():
            ans_text = "No response generated."
        else:
            ans_text = str(ans_text)

        return {
            "intent": intent,
            "answer": ans_text,
            "tool_result": tool_result,
            "execution_time": elapsed,
        }
