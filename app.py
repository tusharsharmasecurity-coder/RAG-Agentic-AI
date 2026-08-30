# app.py – single‑file entry point (keeps your existing import error handling)
import sys, traceback
import streamlit as st

try:
    from ui.styles import load_css          # keep your own loader if you wish
    from ui.sidebar import show_sidebar
    from ui.assistant_page import assistant_page
    from ui.upload_page import upload_page
except Exception:        # pragma: no cover
    with open("exception.log","w",encoding="utf-8") as f:
        f.write("Failed to import UI modules.\n")
        traceback.print_exc(file=f)
    st.error("Application import failed. Check exception.log.")
    st.stop()

# -----------------------------------------------------------------
# PAGE CONFIG
# -----------------------------------------------------------------
st.set_page_config(page_title="Delhivery AI Enterprise", page_icon="🚚",
                   layout="wide", initial_sidebar_state="expanded")

# -----------------------------------------------------------------
# CSS – the tiny utils file runs automatically when imported
# -----------------------------------------------------------------
import utils   # this triggers the st.markdown CSS block

# -----------------------------------------------------------------
# SIDEBAR (your existing function – unchanged)
# -----------------------------------------------------------------
try:
    print(">>> NEW SIDEBAR LOADED", flush=True)
    show_sidebar()
except Exception:
    with open("exception.log","w",encoding="utf-8") as f:
        f.write("Sidebar rendering failed.\n")
        traceback.print_exc(file=f)
    st.error("Sidebar failed. Check exception.log.")
    st.stop()

# -----------------------------------------------------------------
# NAVIGATION
# -----------------------------------------------------------------
page = st.sidebar.radio("Navigation",
                        ["Assistant","Upload Center"],
                        label_visibility="collapsed")

# -----------------------------------------------------------------
# ROUTING
# -----------------------------------------------------------------
if page == "Assistant":
    try:
        assistant_page()
    except Exception:
        with open("exception.log","w",encoding="utf-8") as f:
            f.write("assistant_page() failed.\n")
            traceback.print_exc(file=f)
        st.error("Assistant page encountered an error. Check exception.log.")

elif page == "Upload Center":
    try:
        upload_page()
    except Exception:
        with open("exception.log","w",encoding="utf-8") as f:
            f.write("upload_page() failed.\n")
            traceback.print_exc(file=f)
        st.error("Upload Center encountered an error. Check exception.log.")
