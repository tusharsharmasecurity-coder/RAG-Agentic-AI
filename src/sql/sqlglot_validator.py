from __future__ import annotations

from typing import Any

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError


class SQLGlotValidator:
    """AST-based read-only SQL validation for the MySQL analytics path."""

    PROHIBITED_STATEMENTS = (
        exp.Alter,
        exp.Create,
        exp.Delete,
        exp.Drop,
        exp.Insert,
        exp.TruncateTable,
        exp.Update,
    )

    def __init__(self, dialect: str = "mysql"):
        self.dialect = dialect

    def validate(self, sql: str) -> dict[str, Any]:
        try:
            statements = sqlglot.parse(sql, read=self.dialect)
        except ParseError as error:
            return self._invalid(
                reason=f"SQL parse failure: {error}",
                statement_type=None,
            )

        if len(statements) != 1:
            return self._invalid(
                reason="Only one read-only SQL statement is allowed.",
                statement_type=None,
            )

        ast = statements[0]
        statement_type = ast.key.upper()

        if isinstance(ast, self.PROHIBITED_STATEMENTS):
            return self._invalid(
                reason=f"Prohibited read-only violation: {statement_type}.",
                statement_type=statement_type,
                ast=ast,
            )

        if not isinstance(ast, (exp.Select, exp.Union, exp.Subquery)):
            return self._invalid(
                reason=f"Only SELECT statements are allowed, received {statement_type}.",
                statement_type=statement_type,
                ast=ast,
            )

        if self._sums_awb(ast):
            return self._invalid(
                reason="AWB is an identifier and cannot be aggregated with SUM.",
                statement_type=statement_type,
                ast=ast,
            )

        warnings = []
        if any(isinstance(node, exp.Star) for node in ast.find_all(exp.Star)):
            warnings.append("SELECT * may retrieve unnecessary columns.")

        return {
            "valid": True,
            "reason": "SQLGlot validation passed.",
            "statement_type": statement_type,
            "warnings": warnings,
            "ast": ast,
            "sql": ast.sql(dialect=self.dialect),
        }

    @staticmethod
    def _sums_awb(ast: exp.Expression) -> bool:
        for aggregate in ast.find_all(exp.Sum):
            column = aggregate.this
            if isinstance(column, exp.Column) and column.name.lower() == "awb":
                return True
        return False

    @staticmethod
    def _invalid(
        reason: str,
        statement_type: str | None,
        ast: exp.Expression | None = None,
    ) -> dict[str, Any]:
        return {
            "valid": False,
            "reason": reason,
            "statement_type": statement_type,
            "warnings": [],
            "ast": ast,
            "sql": None,
        }
