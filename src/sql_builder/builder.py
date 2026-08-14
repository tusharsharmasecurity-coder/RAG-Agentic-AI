from src.sql_builder.from_builder import FromBuilder, TableResolutionError


class SQLBuilder:

    def __init__(self, schema_loader=None, from_builder=None):
        self.from_builder = from_builder or FromBuilder(schema_loader=schema_loader)

    @staticmethod
    def _quote_identifier(identifier):
        return f"`{identifier.replace('`', '``')}`"

    def build(self, parsed):
        intent = parsed["intent"]
        metrics = parsed["metrics"]

        if not metrics:
            raise TableResolutionError(
                "Unable to determine a schema column for the query."
            )

        from_clause = self.from_builder.build(metrics)
        quoted_columns = [self._quote_identifier(column) for column in metrics]

        if intent == "count":
            column = quoted_columns[0]
            alias = self._quote_identifier(f"Total_{metrics[0]}")
            return f"SELECT COUNT(DISTINCT {column}) AS {alias} {from_clause}"

        return f"SELECT {', '.join(quoted_columns)} {from_clause}"
