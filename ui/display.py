import pandas as pd
import streamlit as st

from ui.stream import stream_text
from ui .charts import show_chart


def display_answer(answer):

    if isinstance(answer, dict):

        st.success(answer["summary"])

        df = pd.DataFrame(
            answer["rows"],
            columns=answer["columns"]
        )

        st.dataframe(
            df,
            use_container_width=True
        )
        # ----------------------------------
        # Automatic Charts
        # ----------------------------------

        if len(df.columns) == 2:

           first = df.columns[0]
           second = df.columns[1]

    # First column = text
    # Second column = numbers

        if (
        pd.api.types.is_object_dtype(df[first])
        and
        pd.api.types.is_numeric_dtype(df[second])
    ):

         st.markdown("### 📊 Visualization")

         st.bar_chart(
            df.set_index(first)
        )

        show_chart(df)

    else:

     if not isinstance(answer, str):
        answer = str(answer)

     stream_text(answer)