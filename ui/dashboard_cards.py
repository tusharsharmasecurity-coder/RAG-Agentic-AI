import streamlit as st


def show_cards(stats):

    shipments = stats.get("shipments", 0)
    delayed = stats.get("delayed", 0)
    delivered = stats.get("delivered", 0)
    tables = stats.get("tables", 0)

    col1, col2, col3, col4 = st.columns(4)

    cards = [
        ("📦", "Shipments", shipments, "#2563EB"),
        ("⏳", "Delayed", delayed, "#F59E0B"),
        ("✅", "Delivered", delivered, "#22C55E"),
        ("🗄️", "Tables", tables, "#7C3AED"),
    ]

    for col, (icon, label, value, color) in zip(
        [col1, col2, col3, col4],
        cards,
    ):
        with col:
            st.markdown(
                f"""
                <div style="
                    padding: 18px;
                    border-radius: 12px;
                    background: #ffffff;
                    border: 1px solid #e5e7eb;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
                ">
                    <div style="font-size: 26px;">{icon}</div>
                    <div style="
                        font-size: 14px;
                        color: #6b7280;
                        margin-top: 6px;
                    ">
                        {label}
                    </div>
                    <div style="
                        font-size: 28px;
                        font-weight: 700;
                        color: {color};
                        margin-top: 4px;
                    ">
                        {value:,}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )