import streamlit as st


def show_sidebar():
    with st.sidebar:
        st.markdown("<span class='brand-mark'></span><strong style='font-size:1.35rem;color:#182238;'>DELHIVERY</strong>", unsafe_allow_html=True)
        st.caption("Operations intelligence")
        st.space("medium")
        st.caption("WORKSPACE")
