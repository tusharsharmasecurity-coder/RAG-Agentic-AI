import streamlit as st


def load_css():
    st.markdown("""
<style>
:root { --ink:#182238; --muted:#65708a; --line:#e5e9f0; --canvas:#f7f8fb; --accent:#ef443b; --soft-red:#fff0ef; --soft-blue:#eef2ff; }
.stApp { background:var(--canvas); color:var(--ink); }
.block-container { max-width:1440px; padding-top:2.3rem; padding-bottom:3rem; }
section[data-testid="stSidebar"] { background:#fff; border-right:1px solid var(--line); }
section[data-testid="stSidebar"] > div { padding-top:1.15rem; }
[data-testid="stSidebar"] .stRadio label { border-radius:10px; color:#27324a; font-weight:600; padding:0.55rem 0.65rem; }
[data-testid="stSidebar"] .stRadio label:has(input:checked) { background:var(--soft-red); color:var(--accent); }
h1, h2, h3 { color:var(--ink); letter-spacing:-0.025em; }
[data-testid="stMetric"] { background:#fff; border:1px solid var(--line); border-radius:16px; padding:1rem 1.1rem; }
[data-testid="stMetricLabel"] { color:var(--muted); }
[data-testid="stMetricValue"] { color:var(--ink); }
.stButton > button { border:1px solid #dce2ec; border-radius:10px; background:#fff; color:#27324a; font-weight:600; min-height:2.65rem; }
.stButton > button:hover { color:#c8322a; border-color:#ef443b; background:var(--soft-red); }
.stChatInput textarea { background:#fff; border:1px solid #dce2ec; border-radius:12px; }
.stChatMessage { background:#fff; border:1px solid var(--line); border-radius:14px; padding:0.8rem; }
.ops-header { background:#fff; border:1px solid var(--line); border-radius:18px; padding:1.35rem 1.5rem; box-shadow:0 8px 24px rgba(28,39,65,.05); }
.brand-mark { width:38px; height:38px; background:linear-gradient(135deg,#171c27 0 50%,#ef443b 50% 100%); border-radius:8px; display:inline-block; vertical-align:middle; margin-right:10px; }
.eyebrow { color:#7d89a3; font-size:.78rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; }
.header-title { font-size:1.55rem; font-weight:750; color:var(--ink); margin:.2rem 0; }
.header-subtitle { color:var(--muted); font-size:.94rem; }
.dataset-pill { background:var(--soft-blue); color:#4c5d94; border-radius:999px; padding:.5rem .8rem; font-size:.82rem; font-weight:650; display:inline-block; }
.insight-card { background:linear-gradient(110deg,#fff2f0,#e9edff); border-radius:16px; padding:1.2rem 1.35rem; border:1px solid #f0e5ee; }
.section-label { color:#7d89a3; font-size:.78rem; font-weight:750; letter-spacing:.07em; text-transform:uppercase; margin-bottom:.25rem; }
</style>
""", unsafe_allow_html=True)
