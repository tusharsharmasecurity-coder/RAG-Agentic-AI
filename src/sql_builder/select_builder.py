from src.sql_builder.templates import (
    COUNT_TEMPLATE,
    SUM_TEMPLATE,
    AVG_TEMPLATE,
    MAX_TEMPLATE,
    MIN_TEMPLATE,
    SELECT_TEMPLATE,
    SELECT_DISTINCT_TEMPLATE,
)


class SelectBuilder:
    """
    Builds the SELECT clause from the parsed question.
    """

    def build(self, parsed):

        intent = parsed.get("intent", "select")
        metrics = parsed.get("metrics", [])
        distinct = parsed.get("distinct", False)

        # -----------------------------
        # COUNT
        # -----------------------------

        if intent == "count":

            column = metrics[0] if metrics else "*"

            return "SELECT " + COUNT_TEMPLATE.format(
                column=column,
                alias=f"Total_{column}",
            )

        # -----------------------------
        # SUM
        # -----------------------------

        if intent == "sum":

            column = metrics[0]

            return "SELECT " + SUM_TEMPLATE.format(
                column=column,
                alias=f"Total_{column}",
            )

        # -----------------------------
        # AVG
        # -----------------------------

        if intent == "average":

            column = metrics[0]

            return "SELECT " + AVG_TEMPLATE.format(
                column=column,
                alias=f"Average_{column}",
            )

        # -----------------------------
        # MAX
        # -----------------------------

        if intent == "max":

            column = metrics[0]

            return "SELECT " + MAX_TEMPLATE.format(
                column=column,
                alias=f"Maximum_{column}",
            )

        # -----------------------------
        # MIN
        # -----------------------------

        if intent == "min":

            column = metrics[0]

            return "SELECT " + MIN_TEMPLATE.format(
                column=column,
                alias=f"Minimum_{column}",
            )

        # -----------------------------
        # Normal SELECT
        # -----------------------------

        columns = ", ".join(metrics) if metrics else "*"

        if distinct:

            return SELECT_DISTINCT_TEMPLATE.format(
                columns=columns
            )

        return SELECT_TEMPLATE.format(
            columns=columns
        )