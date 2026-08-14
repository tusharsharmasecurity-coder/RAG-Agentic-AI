import streamlit as st

from ui.styles import load_css
from ui.sidebar import show_sidebar
from ui.assistant_page import assistant_page
from ui.upload_page import upload_page


st.set_page_config(
    page_title="Delhivery Operations",
    page_icon=":material/local_shipping:",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_css()
show_sidebar()

page = st.sidebar.radio(
    "Workspace navigation",
    ["Assistant", "Upload Center"],
    label_visibility="collapsed",
)

if page == "Assistant":
    assistant_page()
elif page == "Upload Center":
    upload_page()
