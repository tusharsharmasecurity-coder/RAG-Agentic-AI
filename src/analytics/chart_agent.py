class ChartAgent:

    def decide_chart(self, dataframe):

        cols = dataframe.columns.tolist()

        # Single value → KPI
        if len(cols) == 1:
            return "kpi"

        # Two columns
        if len(cols) == 2:

            first = cols[0].lower()

            if any(x in first for x in [
                "date",
                "day",
                "month",
                "year",
                "time"
            ]):
                return "line"

            return "bar"

        # Three columns
        if len(cols) == 3:
            return "pie"

        return "table"