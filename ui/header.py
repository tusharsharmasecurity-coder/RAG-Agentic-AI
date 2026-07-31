import streamlit as st


def show_header(active_table):

    st.markdown(
        f"""
<div style="
display:flex;
justify-content:space-between;
align-items:center;
padding:20px 28px;
background:#1F2937;
border-radius:18px;
margin-bottom:25px;
box-shadow:0 6px 20px rgba(0,0,0,.25);
">

<div>

<div style="
font-size:34px;
font-weight:700;
color:white;
">
🚚 Delhivery AI Enterprise
</div>

<div style="
font-size:15px;
color:#9CA3AF;
margin-top:6px;
">
Warehouse Intelligence Platform
</div>

</div>

<div style="text-align:right;">

<div style="
display:inline-block;
padding:8px 18px;
background:#2563EB;
color:white;
border-radius:30px;
font-size:14px;
font-weight:600;
margin-bottom:10px;
">
📂 Active Dataset : {active_table}
</div>

<br>

<div style="
color:#9CA3AF;
font-size:13px;
">
👤 Tushar Sharma
</div>

</div>

</div>
""",
        unsafe_allow_html=True,
    )   