import os

# 1. PREVENT C++ & RUST THREAD DEADLOCKS ON WINDOWS
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import sys
import traceback

try:
    import streamlit as st

    # -----------------------------------------------------------------
    # PAGE CONFIG
    # -----------------------------------------------------------------
    st.set_page_config(
        page_title="Delhivery AI Enterprise",
        page_icon="🚚",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    # Hide Streamlit's default developer menu, footer, and add custom styling
    st.markdown(
        """
        <style>
            /* Hide default Streamlit elements */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            
            /* Polish the chat interface */
            .stChatMessage {
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 10px;
            }
            
            /* Style the titles */
            .title {
                font-size: 36px !important;
                font-weight: 700 !important;
                color: #1E3A8A; /* Dark corporate blue */
                margin-bottom: 0px;
            }
            .subtitle {
                font-size: 16px;
                color: #6B7280;
                margin-bottom: 20px;
            }
        </style>
    """,
        unsafe_allow_html=True,
    )
    # -----------------------------------------------------------------
    # MODULE IMPORTS
    # -----------------------------------------------------------------
    import utils
    from ui.sidebar import show_sidebar
    from ui.assistant_page import assistant_page
    from ui.upload_page import upload_page

    # -----------------------------------------------------------------
    # UI EXECUTION
    # -----------------------------------------------------------------
    show_sidebar()

    page = st.sidebar.radio(
        "Navigation",
        ["💬 Assistant", "📤 Upload Center", "📈 Admin Dashboard"],
        index=0,
        key="main_nav_radio",
        label_visibility="collapsed",
    )

    if page == "💬 Assistant":
        assistant_page()
    elif page == "📤 Upload Center":
        upload_page()
    elif page == "📈 Admin Dashboard":
        # Make sure you created the ui/admin_dashboard.py file from my previous message!
        from ui.admin_dashboard import admin_dashboard_page

        admin_dashboard_page()

except BaseException as exc:
    # 2. CATCH FATAL EXITS (Even SystemExit or KeyboardInterrupt)
    with open("crash_debug.log", "w", encoding="utf-8") as f:
        f.write(f"FATAL CRASH [{type(exc).__name__}]: {exc}\n\n")
        traceback.print_exc(file=f)

    # Attempt to show the error on the Streamlit UI before dying
    try:
        import streamlit as st

        st.error(f"System Crash: {type(exc).__name__}. Check crash_debug.log.")
    except:
        pass

    raise
