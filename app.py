print("========== APP.PY LOADED ==========")
import streamlit as st

from ui.styles import load_css
from ui.sidebar import show_sidebar
from ui.assistant_page import assistant_page
from ui.upload_page import upload_page


# ==========================================
# Page Configuration
# ==========================================

st.set_page_config(
    page_title="Delhivery AI Enterprise",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_css()


# ==========================================
# Sidebar
# ==========================================

show_sidebar()

page = st.sidebar.radio(
    "",
    [
        "Assistant",
        "Upload Center",
    ],
)


# ==========================================
# Navigation
# ==========================================

if page == "Assistant":

    assistant_page()

elif page == "Upload Center":

    upload_page()