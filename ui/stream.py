import streamlit as st
import time


def stream_text(text):

    placeholder = st.empty()

    full_text = ""

    for word in text.split():

        full_text += word + " "

        placeholder.markdown(full_text)

        time.sleep(0.02)