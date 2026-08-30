import re

import sqlglot
from sqlglot import exp


class SQLBuilder:
    """
    Converts an LLM response into one clean MySQL SELECT statement.
    """

    def build(self, raw_sql: str) -> str:

        if not raw_sql or not raw_sql.strip():
            raise ValueError(
                "Empty SQL generated."
            )

        text = raw_sql.strip()

        # --------------------------------------------------------
        # Prefer fenced SQL block
        # --------------------------------------------------------

        fenced = re.search(
            r"```(?:sql)?\s*(.*?)```",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )

        if fenced:

            candidates = [
                fenced.group(1).strip()
            ]

        else:

            candidates = [
                text
            ]

            # ----------------------------------------------------
            # Extract from SELECT / WITH
            # ----------------------------------------------------

            match = re.search(
                r"\b(?:SELECT|WITH)\b",
                text,
                flags=re.IGNORECASE,
            )

            if match:

                candidates.append(
                    text[match.start():].strip()
                )

        # --------------------------------------------------------
        # Try candidates
        # --------------------------------------------------------

        last_error = None

        for candidate in candidates:

            candidate = candidate.strip()

            # Remove markdown
            candidate = re.sub(
                r"```(?:sql)?",
                "",
                candidate,
                flags=re.IGNORECASE,
            )

            candidate = candidate.replace(
                "```",
                "",
            ).strip()

            # ----------------------------------------------------
            # Use first semicolon if present
            # ----------------------------------------------------

            if ";" in candidate:

                candidate = (
                    candidate
                    .split(";", 1)[0]
                    .strip()
                    + ";"
                )

            # ----------------------------------------------------
            # Parse directly
            # ----------------------------------------------------

            try:

                expression = (
                    sqlglot.parse_one(
                        candidate,
                        read="mysql",
                    )
                )

                if not isinstance(
                    expression,
                    exp.Query,
                ):
                    raise ValueError(
                        "Only SELECT/WITH queries are allowed."
                    )

                return expression.sql(
                    dialect="mysql",
                    pretty=True,
                )

            except Exception as exc:

                last_error = exc

        # --------------------------------------------------------
        # Line-based fallback
        # --------------------------------------------------------

        sql_match = re.search(
            r"\b(?:SELECT|WITH)\b[\s\S]*",
            text,
            flags=re.IGNORECASE,
        )

        if sql_match:

            lines = (
                sql_match.group(0)
                .splitlines()
            )

            sql_lines = []

            for line in lines:

                clean_line = line.strip()

                if not clean_line:
                    continue

                sql_lines.append(
                    clean_line
                )

                candidate = "\n".join(
                    sql_lines
                )

                try:

                    expression = (
                        sqlglot.parse_one(
                            candidate,
                            read="mysql",
                        )
                    )

                    if isinstance(
                        expression,
                        exp.Query,
                    ):

                        return expression.sql(
                            dialect="mysql",
                            pretty=True,
                        )

                except Exception:
                    continue

        raise ValueError(
            "Unable to extract valid SQL "
            f"from model response: {last_error}"
        )