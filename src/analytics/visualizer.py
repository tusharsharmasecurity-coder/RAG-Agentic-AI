import pandas as pd
import plotly.express as px


class Visualizer:

    def bar(self, df):

        if len(df.columns) < 2:
            return None

        fig = px.bar(
            df,
            x=df.columns[0],
            y=df.columns[1]
        )

        return fig

    def pie(self, df):

        if len(df.columns) < 2:
            return None

        fig = px.pie(
            df,
            names=df.columns[0],
            values=df.columns[1]
        )

        return fig

    def line(self, df):

        if len(df.columns) < 2:
            return None

        fig = px.line(
            df,
            x=df.columns[0],
            y=df.columns[1]
        )

        return fig