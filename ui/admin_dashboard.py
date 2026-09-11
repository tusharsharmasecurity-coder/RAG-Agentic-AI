import streamlit as st
import pandas as pd
import time

def admin_dashboard_page():
    st.title("📈 AI Observability Dashboard")
    st.markdown("Live monitoring of Agentic AI performance and user queries.")
    
    st.divider()

    # 1. Live Top-Level Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Total Queries (Today)", value="142", delta="+12%")
    with col2:
        st.metric(label="Avg Execution Time", value="1.84s", delta="-0.2s", delta_color="inverse")
    with col3:
        st.metric(label="SQL Fallback Rate", value="4.2%", delta="-1.1%", delta_color="inverse")
    with col4:
        st.metric(label="Active Users", value="8")

    st.divider()

    # 2. AI Performance Charts (Visual Layout)
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("### 🎯 Intent Distribution")
        # Placeholder data: Replace this later with self.metrics from your agent
        chart_data = pd.DataFrame({
            "Intents": ["SQL Query", "RAG / Policy", "General Chat", "Error"],
            "Count": [85, 42, 12, 3]
        }).set_index("Intents")
        st.bar_chart(chart_data, color="#1E3A8A")

    with col_chart2:
        st.markdown("### ⏱️ Agent Latency (Last 10 Queries)")
        latency_data = pd.DataFrame({
            "Query": [f"Q{i}" for i in range(1, 11)],
            "Seconds": [1.2, 1.5, 2.1, 0.8, 1.4, 3.2, 1.1, 0.9, 1.6, 1.3]
        }).set_index("Query")
        st.line_chart(latency_data, color="#10B981")

    # 3. Live Query Audit Log
    st.markdown("### 🕵️ Live Query Audit Log")
    audit_data = pd.DataFrame([
        {"Time": "14:32:01", "User": "Tushar S.", "Intent": "SQL", "Question": "Show total shipments for TATACLICK", "Status": "✅ Success"},
        {"Time": "14:28:44", "User": "Tushar S.", "Intent": "RAG", "Question": "What is the damaged goods SOP?", "Status": "✅ Success"},
        {"Time": "14:15:12", "User": "Rahul M.", "Intent": "ERROR", "Question": "Drop table shipments", "Status": "❌ Blocked"},
    ])
    st.dataframe(audit_data, use_container_width=True, hide_index=True)