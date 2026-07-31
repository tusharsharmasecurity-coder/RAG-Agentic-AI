import streamlit as st


def show_cards(stats):

    col1, col2, col3, col4 = st.columns(4)

    cards = [
        ("📦", "Shipments", stats["shipments"], "#2563EB"),
        ("⏳", "Delayed", stats["delayed"], "#F59E0B"),
        ("✅", "Delivered", stats["delivered"], "#22C55E"),
        ("🗄️", "Tables", stats["tables"], "#7C3AED"),
    ]

    for col, (icon, title, value, color) in zip(
        [col1, col2, col3, col4],
        cards,
    ):

        with col:

            st.markdown(
                f"""
<div style="
background:#1f2937;
padding:20px;
border-radius:16px;
border-top:5px solid {color};
box-shadow:0 6px 16px rgba(0,0,0,.25);
">

<div style="font-size:30px;">{icon}</div>

<div style="color:#9CA3AF;font-size:15px;margin-top:8px;">
{title}
</div>

<div style="font-size:38px;font-weight:700;color:white;">
{value}
</div>

</div>
""",
                unsafe_allow_html=True,
            )