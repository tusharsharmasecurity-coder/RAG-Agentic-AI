import streamlit as st

def load_css():

    st.markdown("""
<style>

/* ---------- Main ---------- */

.stApp{

    background:#111827;

    color:#F9FAFB;

}

/* ---------- Sidebar ---------- */

section[data-testid="stSidebar"]{

    background:#1E293B;

    border-right:1px solid #334155;

}

/* ---------- Header ---------- */

.header{

    background:linear-gradient(90deg,#0057B8,#009FE3);

    padding:30px;

    border-radius:20px;

    color:white;

    box-shadow:0 8px 25px rgba(0,0,0,.35);

}

/* ---------- KPI Cards ---------- */

.metric-card{

    background:#1F2937;

    border-radius:18px;

    padding:22px;

    border:1px solid #374151;

    transition:.3s;

    text-align:center;

}

.metric-card:hover{

    transform:translateY(-5px);

    border:1px solid #00AEEF;

    box-shadow:0px 10px 25px rgba(0,174,239,.25);

}

.metric-title{

    color:#9CA3AF;

    font-size:15px;

}

.metric-value{

    color:white;

    font-size:34px;

    font-weight:bold;

}

/* ---------- Chat ---------- */

.stChatInput{

    background:#1F2937;

}

/* ---------- Buttons ---------- */

.stButton>button{

    background:#0057B8;

    color:white;

    border:none;

    border-radius:10px;

}

.stButton>button:hover{

    background:#0077CC;

}

</style>
""", unsafe_allow_html=True)