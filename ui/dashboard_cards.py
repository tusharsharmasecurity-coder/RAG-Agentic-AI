import streamlit as st


def show_cards(stats):
    st.markdown("<div class='section-label'>Delivery overview</div>", unsafe_allow_html=True)
    metrics = [
        ("Total shipments", stats["shipments"], ":material/local_shipping:"),
        ("Delayed shipments", stats["delayed"], ":material/schedule:"),
        ("Delivered", stats["delivered"], ":material/task_alt:"),
        ("Data tables", stats["tables"], ":material/table_chart:"),
    ]
    for col, (title, value, icon) in zip(st.columns(4), metrics):
        with col:
            st.metric(title, value, border=True)
            st.caption(icon)
