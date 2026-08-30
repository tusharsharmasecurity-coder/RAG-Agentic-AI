# ui/assistant_page.py – minimal UI, no duplicate content
import streamlit as st
from src.database import Database
from src.dashboard import Dashboard
from src.api_client import ask_agent
from ui.dashboard_cards import show_cards


def assistant_page():
    # ------------------------------
    #  Console line (optional – shows in the terminal that launched Streamlit)
    # ------------------------------
    print("[ASSISTANT] Page started", flush=True)  # <‑‑ changed from st.print

    # ------------------------------
    #  Database
    # ------------------------------
    try:
        db = Database()
        print("[ASSISTANT] Database connected", flush=True)  # <‑‑ changed
    except Exception as exc:
        st.error("Database connection failed.")
        print(
            f"[DATABASE ERROR] {type(exc).__name__}: {exc}", flush=True
        )  # <‑‑ changed
        return

    # ------------------------------
    #  Dashboard
    # ------------------------------
    try:
        dashboard = Dashboard(db)
        print("[ASSISTANT] Dashboard created", flush=True)  # <‑‑ changed
    except Exception as exc:
        st.error("Dashboard initialization failed.")
        print(
            f"[DASHBOARD ERROR] {type(exc).__name__}: {exc}", flush=True
        )  # <‑‑ changed
        try:
            db.close()
        except Exception:
            pass
        return

    # ------------------------------
    #  Active table
    # ------------------------------
    try:
        active_table = dashboard.get_active_table()
        print(f"[ASSISTANT] Active Table: {active_table}", flush=True)  # <‑‑ changed
    except Exception as exc:
        active_table = "Unknown"
        print(
            f"[ACTIVE TABLE ERROR] {type(exc).__name__}: {exc}", flush=True
        )  # <‑‑ changed

    # ------------------------------
    #  Header (simple, no duplicate)
    # ------------------------------
    st.markdown(
        "<div class='title'>🚚 Delhivery AI Assistant</div>", unsafe_allow_html=True
    )
    st.markdown(
        f"<div class='subtitle'>Active data table: `{active_table}`</div>",
        unsafe_allow_html=True,
    )

    # ------------------------------
    #  Dashboard stats (cards)
    # ------------------------------
    try:
        stats = dashboard.get_stats()
        stats = {
            "shipments": stats.get("shipments", 0),
            "delayed": stats.get("delayed", 0),
            "delivered": stats.get("delivered", 0),
            "tables": stats.get("tables", 0),
        }
        show_cards(stats)  # your existing card function
    except Exception as exc:
        st.warning("Dashboard statistics are temporarily unavailable.")
        print(f"[STATS ERROR] {type(exc).__name__}: {exc}", flush=True)  # <‑‑ changed

    st.divider()

    # ------------------------------
    #  CHAT HISTORY
    # ------------------------------
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # show previous messages
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ------------------------------
    #  USER INPUT
    # ------------------------------
    user_message = st.chat_input("Ask Delhivery AI anything about your logistics data…")

    if user_message:
        # 1️⃣ show user message immediately
        with st.chat_message("user"):
            st.markdown(user_message)

        # 2️⃣ store user message
        st.session_state.chat_messages.append({"role": "user", "content": user_message})

        # 3️⃣ build conversation history for the LLM
        history = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.chat_messages[
                :-1
            ]  # all but the just‑sent user msg
        ]

        # 4️⃣ call the LLM (the function you already import)
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):

                try:
                    response = ask_agent(user_message)

                    result = response["result"]

                    answer = result.get("answer", "No response generated.")

                    intent = result.get("intent", "UNKNOWN")

                    execution_time = result.get("execution_time", 0)

                    tool_result = result.get("tool_result")

                except Exception as exc:

                    answer = f"Agent API error: {exc}"

                    intent = "ERROR"

                    execution_time = 0

                    tool_result = None

                # ------------------------------------------------
                # Answer
                # ------------------------------------------------

                st.markdown(answer)

                # ------------------------------------------------
                # Agent information
                # ------------------------------------------------

                with st.expander("🔎 Agent Details"):

                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric("Intent", intent)

                with col2:
                    st.metric("Execution Time", f"{execution_time:.3f}s")

                # ------------------------------------------------
                # SQL
                # ------------------------------------------------

                if isinstance(tool_result, dict) and tool_result.get("sql"):

                    st.markdown("### Generated SQL")

                    st.code(tool_result["sql"], language="sql")

        # 5️⃣ store assistant reply
        st.session_state.chat_messages.append({"role": "assistant", "content": answer})

    # ------------------------------
    #  CLEAR CHAT button
    # ------------------------------
    if st.button("🗑️ Clear Chat", key="clear_chat"):
        st.session_state.chat_messages = []
        st.rerun()
