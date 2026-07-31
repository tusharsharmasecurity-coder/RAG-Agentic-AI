import streamlit as st

from ui.quick_actions import show_quick_actions
from ui.chat_layout import begin_chat
from ui.header import show_header
from ui.dashboard_cards import show_cards

from src.dashboard import Dashboard
from src.agent import DelhiveryAgent
from src.analytics.dashboard_agent import DashboardAgent
from src.learner import LearningEngine


def assistant_page():

    dashboard = Dashboard()
    dashboard_agent = DashboardAgent()
    agent = DelhiveryAgent()
    learner = LearningEngine()

    stats = dashboard.get_stats()
    active_table = dashboard.get_active_table()

    # -----------------------------
    # Session State
    # -----------------------------

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "dashboard" not in st.session_state:
        st.session_state.dashboard = None

    if "last_tool_result" not in st.session_state:
        st.session_state.last_tool_result = None

    # -----------------------------
    # Header
    # -----------------------------

    show_header(active_table)

    st.divider()

    show_cards(stats)

    st.divider()

    show_quick_actions()

    begin_chat()

    st.divider()

    # ==========================================
    # MAIN LAYOUT
    # ==========================================

    chat_col, analytics_col = st.columns([2, 1], gap="large")

    # ==========================================
    # CHAT
    # ==========================================

    with chat_col:

        # Chat History
        for message in st.session_state.messages:

            with st.chat_message(message["role"]):

                if message["role"] == "user":

                    st.write(message["content"])

                else:

                    result = message["content"]

                    if result.get("answer"):
                        st.write(result["answer"])

        # Chat Input
        question = st.chat_input("Ask Delhivery AI...")

        if question:

            st.session_state.messages.append({"role": "user", "content": question})

            with st.chat_message("user"):
                st.write(question)

            with st.chat_message("assistant"):

                with st.spinner("🤖 Thinking..."):

                    result = agent.ask(question)
                st.json(result)

                if result.get("answer"):
                    st.write(result["answer"])

                if result.get("tool_result"):

                    st.session_state.last_tool_result = result["tool_result"]

                    dashboard_data = dashboard_agent.build(result["tool_result"])

                    if dashboard_data:
                        st.session_state.dashboard = dashboard_data

            st.session_state.messages.append({"role": "assistant", "content": result})

            st.rerun()

    # ==========================================
    # ANALYTICS PANEL
    # ==========================================

    with analytics_col:

        st.subheader("🤖 AI Analytics")

        tool = st.session_state.last_tool_result

        if tool:

            st.metric("Execution Time", f"{tool.get('time', 0)} sec")

            st.metric("Rows Returned", len(tool.get("rows", [])))

            st.metric("Columns", len(tool.get("columns", [])))

            st.divider()

            st.markdown("### 📝 Generated SQL")

            st.code(tool.get("sql", ""), language="sql")

            st.divider()

            st.markdown("### 📄 Summary")

            st.info(tool.get("answer", "No summary available."))

            st.divider()

            st.markdown("### 👍 Feedback")

            log_id = tool.get("log_id")

            if log_id:

                col1, col2 = st.columns(2)

                with col1:

                    if st.button("👍 Helpful", key=f"good_{log_id}"):

                        learner.update_feedback(log_id, 1)

                        st.success("Feedback saved!")

                with col2:

                    if st.button("👎 Wrong", key=f"bad_{log_id}"):

                        learner.update_feedback(log_id, -1)

                        st.warning("Feedback saved!")

        else:

            st.info("Run a SQL query to see AI analytics.")
