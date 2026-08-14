import streamlit as st


def show_quick_actions():
    st.markdown("<div class='section-label'>Quick actions</div>", unsafe_allow_html=True)
    actions = [
        ("Upload data", ":material/upload_file:"),
        ("Analyse shipments", ":material/query_stats:"),
        ("Browse knowledge", ":material/menu_book:"),
        ("View history", ":material/history:"),
    ]
    for col, (label, icon) in zip(st.columns(4), actions):
        with col:
            st.button(label, icon=icon, width="stretch")
