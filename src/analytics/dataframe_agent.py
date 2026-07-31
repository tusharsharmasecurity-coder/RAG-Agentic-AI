from src.analytics.dataframe_memory import dataframe_memory


class DataFrameAgent:

    def run(self, question):

        df = dataframe_memory.get()

        if df is None:
            return None

        question = question.lower()

        # -------------------------
        # Sort
        # -------------------------

        if "sort" in question:

            column = df.columns[-1]

            ascending = "ascending" in question

            df = df.sort_values(
                by=column,
                ascending=ascending
            )

            dataframe_memory.save(df)

            return {
                "answer": "Sorted successfully.",
                "dataframe": df
            }

        # -------------------------
        # Top
        # -------------------------

        if "top" in question:

            number = 5

            words = question.split()

            for word in words:
                if word.isdigit():
                    number = int(word)

            df = df.head(number)

            dataframe_memory.save(df)

            return {
                "answer": f"Showing Top {number} rows.",
                "dataframe": df
            }

        # -------------------------
        # Summary
        # -------------------------

        if "summary" in question:

            return {
                "answer": "Summary generated.",
                "dataframe": df.describe(include="all")
            }

        return None