import pandas as pd
from src.analytics.visualization_agent import VisualizationAgent
from src.analytics.dataframe_memory import dataframe_memory



class DashboardAgent:

    def __init__(self):

        
        self.visual = VisualizationAgent()

    def build(self, sql_result):

        if sql_result is None:
            return None

        columns = sql_result.get("columns", [])
        rows = sql_result.get("rows", [])

        if len(columns) == 0:
            return None

        df = pd.DataFrame(rows, columns=columns)

        # Save dataframe for follow-up questions
        dataframe_memory.save(df)

        # AI decides chart type
        
        chart = self.visual.decide(df)
        dashboard = {

           "dataframe": df,

            "kpis": {

            "Rows": len(df),

            "Columns": len(df.columns)

              },

             "chart": chart

               }

        return dashboard
