import streamlit as st
import pandas as pd
import plotly.express as px


def render_tool_result(tool_result):

    if tool_result is None:
        return

    if tool_result["type"] == "error":
        st.error(tool_result["message"])
        return

    if tool_result["type"] == "table":

        st.markdown(
            '<div class="response-card">',
            unsafe_allow_html=True
        )

        # --------------------
        # SQL
        # --------------------

        if tool_result.get("sql"):

            st.subheader("🧠 Generated SQL")

            st.code(
                tool_result["sql"],
                language="sql"
            )

        # --------------------
        # DataFrame
        # --------------------

        df = pd.DataFrame(
            tool_result["rows"],
            columns=tool_result["columns"]
        )

        # --------------------
        # KPI Cards
        # --------------------

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric("Rows", len(df))

        with c2:
            st.metric(
                "Time",
                f"{tool_result.get('time',0)} sec"
            )

        with c3:
            st.metric(
                "Database",
                "MySQL"
            )

        st.divider()

        # --------------------
        # Table
        # --------------------
        st.info(
           f"Showing {len(df)} rows."
)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        # --------------------
        # Single Value KPI
        # --------------------

        if len(df.columns) == 1 and len(df) == 1:

            st.metric(
                "📊 Query Result",
                df.iloc[0,0]
            )

        # --------------------
        # Auto Chart
        # --------------------

        elif len(df.columns) == 2:

            first = df.columns[0]
            second = df.columns[1]

            if pd.api.types.is_numeric_dtype(df[second]):

                fig = px.bar(
                    df,
                    x=first,
                    y=second,
                    text=second,
                    title="Visualization"
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )