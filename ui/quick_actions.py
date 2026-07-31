import streamlit as st


def show_quick_actions():

    st.subheader("⚡ Quick Actions")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.button(
            "📤 Upload Excel",
            use_container_width=True
        )

    with c2:
        st.button(
            "🗄 SQL Analytics",
            use_container_width=True
        )

    with c3:
        st.button(
            "📚 Knowledge Base",
            use_container_width=True
        )

    with c4:
        st.button(
            "🕘 Upload History",
            use_container_width=True
        )