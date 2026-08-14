import streamlit as st


def show_header(active_table):
    st.markdown(
        f"""
<div class="ops-header">
  <div style="display:flex;justify-content:space-between;align-items:center;gap:24px;">
    <div>
      <div class="eyebrow">Operations workspace</div>
      <div class="header-title">Shipment intelligence</div>
      <div class="header-subtitle">Ask, investigate, and act on your delivery data in one place.</div>
    </div>
    <div style="text-align:right;">
      <div class="dataset-pill">Active dataset · {active_table}</div>
      <div class="header-subtitle" style="margin-top:8px;">Tushar Sharma</div>
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
