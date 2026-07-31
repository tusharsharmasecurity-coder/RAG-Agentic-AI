import streamlit as st

print(">>> NEW SIDEBAR LOADED")

def show_sidebar():

    with st.sidebar:

        st.title("Delhivery AI")

        st.success("Sidebar Loaded Successfully")