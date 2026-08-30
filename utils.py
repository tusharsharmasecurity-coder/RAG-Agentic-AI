# utils.py – minimal CSS so the app looks tidy
import streamlit as st

st.markdown(
    """
<style>
/* ---- basic colour palette – easy to tweak ---- */
:root{
    --primary:#0f2027;      /* dark teal */
    --accent:#2a9d8f;       /* teal */
    --bg:#f4f5f7;          /* light slate */
    --card:#ffffff;
    --text:#2d3436;
    --muted:#8492a6;
}
.stApp{background-color:var(--bg);color:var(--text);}
.card{background:var(--card);border-radius:8px;padding:0.8rem 1rem;margin-bottom:0.8rem;box-shadow:0 2px 4px rgba(0,0,0,0.08);}
.title{color:var(--primary);font-size:1.6rem;margin-bottom .4rem;}
.subtitle{color:var(--muted);font-size:.9rem;margin-bottom 1rem;}
/* chat bubbles */
.stChatMessage{border-radius:10px;padding:0.6rem 1rem;margin:0.4rem 0;background:var(--card);}
.stChatMessage[data-role="user"]{margin-left:auto;max-width:80%;}
.stChatMessage[data-role="assistant"]{margin-right:auto;max-width:80%;}
/* buttons */
.stButton>button{border-radius:6px;background:var(--accent);color:#fff;border:none;font-weight:500;}
.stButton>button:hover{background:#26887e;}
/* sidebar */
section[data-testid="stSidebar"]{background:var(--primary);}
section[data-testid="stSidebar"] .stMarkdown,section[data-testid="stSidebar"] label,section[data-testid="stSidebar"] .stSelectbox label{color:#e9c46a;}
</style>
""",
    unsafe_allow_html=True,
)
