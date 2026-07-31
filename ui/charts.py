import pandas as pd
import streamlit as st


def show_chart(df: pd.DataFrame):

    if len(df.columns) != 2:
        return

    first = df.columns[0]
    second = df.columns[1]

    if pd.api.types.is_numeric_dtype(df[second]):

        st.bar_chart(
            df,
            x=first,
            y=second,
            use_container_width=True
        )