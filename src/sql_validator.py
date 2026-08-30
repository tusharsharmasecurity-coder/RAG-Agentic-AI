import re
from typing import Dict, List, Optional

import sqlglot
from sqlglot import exp


class SQLValidator:
    """
    MySQL SELECT-only validator.

    Validates:
    - SQL syntax
    - single statement
    - SELECT-only
    - destructive operations
    - referenced tables
    - referenced columns
    - AWB aggregation safety
    """

    def __init__(self, schema_text: str):
        self.tables: Dict[str, Dict[str, str]] = {}
        self.column_lookup: Dict[str, List[tuple[str, str]]] = {}

        self.load_schema(schema_text)

    # ============================================================
    # NORMALIZATION
    # ============================================================

    @staticmethod
    def normalize(text: str) -> str:
        return re.sub(
            r"[^a-z0-9]",
            "",
            text.lower(),
        )

    # ============================================================
    # LOAD SCHEMA
    # ============================================================

    def load_schema(self, schema_text: str) -> None:

        current_table: Optional[str] = None

        for raw_line in schema_text.splitlines():

            line = raw_line.strip()

            if not line:
                continue

            if line.lower().startswith("table:"):

                current_table = line.split(":", 1)[1].strip()

                self.tables[current_table] = {}

                continue

            if line.startswith("-") and current_table:

                column = line[1:].strip()

                normalized = self.normalize(column)

                self.tables[current_table][normalized] = column

                self.column_lookup.setdefault(
                    normalized,
                    [],
                ).append(
                    (
                        current_table,
                        column,
                    )
                )

    # ============================================================
    # VALIDATE
    # ============================================================

    def validate(
        self,
        sql: str,
        question: Optional[str] = None,
    ) -> dict:

        if not sql or not sql.strip():
            return self._fail("SQL is empty.")

        # --------------------------------------------------------
        # SQLGlot parsing
        # --------------------------------------------------------

        try:

            statements = sqlglot.parse(
                sql,
                read="mysql",
            )

        except Exception as exc:

            return self._fail(f"Invalid MySQL syntax: {exc}")

        if len(statements) != 1 or statements[0] is None:

            return self._fail("Exactly one SQL statement is allowed.")

        statement = statements[0]

        # --------------------------------------------------------
        # SELECT only
        # --------------------------------------------------------

        if not isinstance(
            statement,
            exp.Query,
        ):

            return self._fail("Only SELECT statements are allowed.")

        # --------------------------------------------------------
        # Destructive SQL
        # --------------------------------------------------------

        destructive = (
            exp.Delete,
            exp.Update,
            exp.Insert,
            exp.Create,
            exp.Drop,
            exp.Alter,
        )

        if any(isinstance(node, destructive) for node in statement.walk()):

            return self._fail("Destructive SQL is not allowed.")

        # --------------------------------------------------------
        # Tables
        # --------------------------------------------------------

        cte_names = {cte.alias_or_name.lower() for cte in statement.find_all(exp.CTE)}

        allowed_tables = {name.lower() for name in self.tables}

        referenced_tables: List[str] = []
        table_aliases: Dict[str, str] = {}

        for table in statement.find_all(exp.Table):

            table_name = table.name.lower()

            if table_name in cte_names:
                continue

            if table_name not in allowed_tables:

                return self._fail(
                    f"Unknown table: {table.name}",
                    score=20,
                )

            referenced_tables.append(table.name)

            # Actual table name
            table_aliases[table_name] = table.name

            # Alias
            alias = table.alias_or_name

            if alias:
                table_aliases[alias.lower()] = table.name

        # --------------------------------------------------------
        # Column aliases created by SELECT
        # --------------------------------------------------------

        select_aliases = set()

        for alias in statement.find_all(exp.Alias):

            alias_name = alias.alias

            if alias_name:
                select_aliases.add(self.normalize(alias_name))

        # --------------------------------------------------------
        # Column validation
        # --------------------------------------------------------

        column_error = self._validate_columns(
            statement=statement,
            referenced_tables=referenced_tables,
            table_aliases=table_aliases,
            select_aliases=select_aliases,
            cte_names=cte_names,
        )

        if column_error:
            return self._fail(
                column_error,
                score=10,
            )

        # --------------------------------------------------------
        # AWB aggregation protection
        # --------------------------------------------------------

        if self._uses_awb_math(statement):

            return self._fail(
                "AWB is an identifier and "
                "cannot be aggregated with "
                "SUM, AVG, MIN or MAX.",
                score=0,
            )

        return {
            "score": 100,
            "decision": "PASS",
            "reason": "SQL Valid",
            "retry": False,
        }

    # ============================================================
    # COLUMN VALIDATION
    # ============================================================

    def _validate_columns(
        self,
        statement,
        referenced_tables: List[str],
        table_aliases: Dict[str, str],
        select_aliases: set,
        cte_names: set,
    ) -> Optional[str]:

        # Normalize referenced table names
        referenced_table_objects = []

        for referenced in referenced_tables:

            for actual_table in self.tables:

                if actual_table.lower() == referenced.lower():

                    referenced_table_objects.append(actual_table)

                    break

        for column in statement.find_all(exp.Column):

            column_name = column.name

            # SELECT *
            if column_name == "*":
                continue

            normalized_column = self.normalize(column_name)

            # Alias generated by SELECT
            if normalized_column in select_aliases:
                continue

            # ----------------------------------------------------
            # Qualified column: table.column
            # ----------------------------------------------------

            if column.table:

                qualifier = column.table.lower()

                if qualifier in cte_names:
                    continue

                actual_table = table_aliases.get(qualifier)

                if actual_table is None:

                    return f"Unknown table qualifier " f"'{column.table}'."

                table_columns = self.tables.get(
                    actual_table,
                    {},
                )

                if normalized_column not in table_columns:

                    return (
                        f"Unknown column "
                        f"'{column_name}' "
                        f"in table "
                        f"'{actual_table}'."
                    )

                continue

            # ----------------------------------------------------
            # Unqualified column
            # ----------------------------------------------------

            matches = []

            for actual_table in referenced_table_objects:

                columns = self.tables.get(
                    actual_table,
                    {},
                )

                if normalized_column in columns:

                    matches.append(actual_table)

            # If there is a real matching column,
            # it is valid.
            if matches:
                continue

            # Global fallback for queries where
            # SQLGlot doesn't expose table context cleanly.
            global_matches = self.column_lookup.get(
                normalized_column,
                [],
            )

            if global_matches:
                continue

            return f"Unknown column " f"'{column_name}'."

        return None

    # ============================================================
    # AWB MATH
    # ============================================================

    @staticmethod
    def _uses_awb_math(
        statement,
    ) -> bool:

        aggregate_types = (
            exp.Sum,
            exp.Avg,
            exp.Min,
            exp.Max,
        )

        for node in statement.walk():

            if not isinstance(
                node,
                aggregate_types,
            ):
                continue

            for column in node.find_all(exp.Column):

                if column.name.lower() == "awb":
                    return True

        return False

    # ============================================================
    # FAILURE
    # ============================================================

    @staticmethod
    def _fail(
        reason: str,
        score: int = 0,
    ) -> dict:

        return {
            "score": score,
            "decision": "FAIL",
            "reason": reason,
            "retry": True,
        }
