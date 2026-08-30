import sqlglot


class SQLOptimizer:
    """Conservative SQL normalization using SQLGlot."""

    def optimize(self, sql: str) -> str:

        expression = sqlglot.parse_one(
            sql,
            read="mysql",
        )

        return expression.sql(
            dialect="mysql",
            pretty=True,
        )