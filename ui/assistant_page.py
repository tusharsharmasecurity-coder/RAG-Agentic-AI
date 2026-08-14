import time

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
    start = time.time()
    agent = DelhiveryAgent()
    learner = LearningEngine()

    stats = dashboard.get_stats()
    active_table = dashboard.get_active_table()
    print(f"Dashboard Build Time: {time.time() - start:.2f} sec")

    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("dashboard", None)
    st.session_state.setdefault("last_tool_result", None)

    show_header(active_table)
    st.space("medium")
    show_cards(stats)
    st.space("small")
    show_quick_actions()
    st.space("medium")

    chat_col, analytics_col = st.columns([2, 1], gap="large")

    with chat_col:
        begin_chat()
        st.space("small")
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    st.write(message["content"])
                elif message["content"].get("answer"):
                    st.write(message["content"]["answer"])

        question = st.chat_input("Ask about a shipment, delay, SOP, or dataset...")
        if question:
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.write(question)
            with st.chat_message("assistant"):
                with st.spinner("Investigating your delivery data..."):
                    result = agent.ask(question)
                if result.get("answer"):
                    st.write(result["answer"])
                if result.get("tool_result"):
                    st.session_state.last_tool_result = result["tool_result"]
                    dashboard_data = dashboard_agent.build(result["tool_result"])
                    if dashboard_data:
                        st.session_state.dashboard = dashboard_data
            st.session_state.messages.append({"role": "assistant", "content": result})
            st.rerun()

    with analytics_col:
        st.markdown("<div class='section-label'>Investigation panel</div>", unsafe_allow_html=True)
        st.subheader("AI analytics", divider=False)
        tool = st.session_state.last_tool_result
        if tool:
            st.metric("Execution time", f"{tool.get('time', 0)} sec", border=True)
            st.metric("Rows returned", len(tool.get("rows", [])), border=True)
            st.metric("Columns", len(tool.get("columns", [])), border=True)
            st.space("small")
            st.markdown("**Generated SQL**")
            st.code(tool.get("sql", ""), language="sql")
            st.markdown("**Summary**")
            st.info(tool.get("answer", "No summary available."), icon=":material/auto_awesome:")
            st.markdown("**Was this useful?**")
            log_id = tool.get("log_id")
            if log_id:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Helpful", icon=":material/thumb_up:", key=f"good_{log_id}"):
                        learner.update_feedback(log_id, 1)
                        st.success("Feedback saved!")
                with col2:
                    if st.button("Incorrect", icon=":material/thumb_down:", key=f"bad_{log_id}"):
                        learner.update_feedback(log_id, -1)
                        st.warning("Feedback saved!")
        else:
            st.info("Run a shipment question to see query details and results here.", icon=":material/query_stats:")
