import streamlit as st


def begin_chat():
    st.markdown("""
<div class="insight-card">
  <div class="section-label">AI summary</div>
  <div style="font-size:1.1rem;font-weight:700;color:#182238;">Your delivery co-pilot is ready</div>
  <p style="margin:.35rem 0 0;color:#536078;">Ask about shipment performance, delays, warehouse trends, or your uploaded data.</p>
</div>
""", unsafe_allow_html=True)
