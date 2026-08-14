import pandas as pd


class VisualizationAgent:

    def decide(self, df):

        if df.empty:

            return {
                "chart": "table",
                "reason": "Empty dataframe"
            }

        numeric = list(df.select_dtypes(include="number").columns)

        categorical = list(df.select_dtypes(exclude="number").columns)

        # KPI
        if len(df.columns) == 1 and len(numeric) == 1:

            return {
                "chart": "kpi",
                "reason": "Single numeric value"
            }

        # Line
        if len(numeric) == 1:

            for c in df.columns:

                if "date" in c.lower() or "lsd" in c.lower():

                    return {
                        "chart": "line",
                        "reason": "Time series"
                    }

        # Pie
        if len(df) <= 8 and len(categorical) == 1 and len(numeric) == 1:

            return {
                "chart": "pie",
                "reason": "Category distribution"
            }

        # Bar
        if len(categorical) >= 1 and len(numeric) >= 1:

            return {
                "chart": "bar",
                "reason": "Category comparison"
            }

        return {
            "chart": "table",
            "reason": "Fallback"
        }