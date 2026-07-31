import streamlit as st

def begin_chat():

    st.markdown("""
    <div style="
        background:#1F2937;
        padding:20px;
        border-radius:18px;
        margin-top:20px;
        margin-bottom:20px;
        border:1px solid #334155;
    ">
    <h3 style="margin:0;color:white;">
    💬 AI Workspace
    </h3>

    <p style="color:#94A3B8;">
    Ask questions about your warehouse, shipments or uploaded datasets.
    </p>

    </div>
    """, unsafe_allow_html=True)