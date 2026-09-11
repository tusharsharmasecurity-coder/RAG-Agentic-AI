# ui/assistant_page.py – minimal UI with streaming animation & rich details
import time
import uuid  # ⭐ NEW: For generating unique session memory IDs
import pandas as pd  # ⭐ NEW: For CSV data export
import streamlit as st
from src.database import Database
from src.dashboard import Dashboard
from src.api_client import ask_agent
from ui.dashboard_cards import show_cards


def stream_text_generator(text: str, delay: float = 0.02):
    """Generates words one-by-one to create a smooth streaming typing effect."""
    words = text.split(" ")
    for i, word in enumerate(words):
        yield word + (" " if i < len(words) - 1 else "")
        time.sleep(delay)


def assistant_page():
    # ------------------------------
    #  Console line
    # ------------------------------
    print("[ASSISTANT] Page started", flush=True)

    # ------------------------------
    #  Database
    # ------------------------------
    try:
        db = Database()
        print("[ASSISTANT] Database connected", flush=True)
    except Exception as exc:
        st.error("Database connection failed.")
        print(f"[DATABASE ERROR] {type(exc).__name__}: {exc}", flush=True)
        return

    # ------------------------------
    #  Dashboard
    # ------------------------------
    try:
        dashboard = Dashboard(db)
        print("[ASSISTANT] Dashboard created", flush=True)
    except Exception as exc:
        st.error("Dashboard initialization failed.")
        print(f"[DASHBOARD ERROR] {type(exc).__name__}: {exc}", flush=True)
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
        print(f"[ASSISTANT] Active Table: {active_table}", flush=True)
    except Exception as exc:
        active_table = "Unknown"
        print(f"[ACTIVE TABLE ERROR] {type(exc).__name__}: {exc}", flush=True)

    # ------------------------------
    #  Header
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
        show_cards(stats)
    except Exception as exc:
        st.warning("Dashboard statistics are temporarily unavailable.")
        print(f"[STATS ERROR] {type(exc).__name__}: {exc}", flush=True)

    st.divider()

    # ------------------------------
    #  CHAT HISTORY & MEMORY INIT
    # ------------------------------
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
        
    # ⭐ NEW: Initialize a unique Thread ID for this user session's memory
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())

    # show previous messages
    for msg_idx, msg in enumerate(st.session_state.chat_messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
            # ⭐ NEW: Show tables for past SQL queries in history
            if msg.get("tool_result") and isinstance(msg["tool_result"], dict):
                data = msg["tool_result"].get("data") or msg["tool_result"].get("results")
                if data:
                    st.dataframe(pd.DataFrame(data), use_container_width=True)
            
            # If historical message has agent details attached, render them
            if msg.get("tool_result") or msg.get("intent"):
                with st.expander("🔎 Agent Details"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Intent", msg.get("intent", "UNKNOWN"))
                    with col2:
                        st.metric("Execution Time", f"{msg.get('execution_time', 0.0):.3f}s")
                    
                    if isinstance(msg.get("tool_result"), dict) and msg["tool_result"].get("sql"):
                        st.markdown("### Generated SQL")
                        st.code(msg["tool_result"]["sql"], language="sql")

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

        # 3️⃣ call the LLM and Stream Answer
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                try:
                    # ⭐ NEW: Pass the thread_id to the API client for memory
                    response = ask_agent(user_message, thread_id=st.session_state.thread_id)

                    answer = response.get("answer", "No response generated.")
                    intent = response.get("intent", "UNKNOWN")
                    execution_time = response.get("execution_time", 0.0)
                    tool_result = response.get("tool_result")

                except Exception as exc:
                    answer = f"Agent API error: {exc}"
                    intent = "ERROR"
                    execution_time = 0.0
                    tool_result = None

            # 4️⃣ STREAM THE ANSWER WORD-BY-WORD
            if hasattr(st, "write_stream"):
                st.write_stream(stream_text_generator(answer))
            else:
                message_placeholder = st.empty()
                full_response = ""
                for word in answer.split(" "):
                    full_response += word + " "
                    message_placeholder.markdown(full_response + "▌")
                    time.sleep(0.02)
                message_placeholder.markdown(answer)

            # ⭐ NEW: 4.5 DISPLAY TABLE AND CSV DOWNLOAD BUTTON
            if isinstance(tool_result, dict):
                # Try to extract data/results from your SQL tool output
                sql_data = tool_result.get("data") or tool_result.get("results")
                if sql_data:
                    df = pd.DataFrame(sql_data)
                    st.markdown("### 📊 Query Results")
                    st.dataframe(df, use_container_width=True)
                    
                    # Convert to CSV and create download button
                    csv_data = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Data as CSV",
                        data=csv_data,
                        file_name=f"delhivery_export_{int(time.time())}.csv",
                        mime="text/csv",
                        key=f"dl_live_{int(time.time())}"
                    )

            # 5️⃣ AGENT DETAILS EXPANDER
            with st.expander("🔎 Agent Details"):
                col1, col2 = st.columns(2)

                with col1:
                    st.metric("Intent", intent)

                with col2:
                    st.metric("Execution Time", f"{execution_time:.3f}s")

                if isinstance(tool_result, dict) and tool_result.get("sql"):
                    st.markdown("### Generated SQL")
                    st.code(tool_result["sql"], language="sql")

        # 6️⃣ store assistant reply in history
        st.session_state.chat_messages.append({
            "role": "assistant", 
            "content": answer,
            "intent": intent,
            "execution_time": execution_time,
            "tool_result": tool_result
        })

    # ------------------------------
    #  CLEAR CHAT button
    # ------------------------------
    if st.button("🗑️ Clear Chat", key="clear_chat"):
        st.session_state.chat_messages = []
        # Clear the memory thread ID too, so it starts fresh!
        st.session_state.thread_id = str(uuid.uuid4())
        st.rerun()