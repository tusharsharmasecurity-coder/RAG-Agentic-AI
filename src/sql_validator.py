import re


class SQLValidator:

    SQL_KEYWORDS = {
        "select",
        "from",
        "where",
        "group",
        "by",
        "order",
        "limit",
        "having",
        "and",
        "or",
        "not",
        "in",
        "like",
        "between",
        "is",
        "null",
        "distinct",
        "asc",
        "desc",
        "as",
        "on",
        "join",
        "left",
        "right",
        "inner",
        "outer",
        "union",
        "case",
        "when",
        "then",
        "else",
        "end",
        "exists",
    }

    SQL_FUNCTIONS = {
        "count",
        "sum",
        "avg",
        "min",
        "max",
        "upper",
        "lower",
        "length",
        "round",
        "concat",
    }

    BLOCKED = {
        "delete",
        "update",
        "insert",
        "drop",
        "alter",
        "truncate",
        "create",
        "grant",
        "revoke",
    }

    def __init__(self, schema_text):

        self.tables = {}
        self.column_lookup = {}
        self.load_schema(schema_text)

    # -------------------------------------
    # Read schema
    # -------------------------------------
    def normalize(self, text):
        return re.sub(r"[^a-z0-9]", "", text.lower())

    def load_schema(self, schema_text):

        current_table = None

        for line in schema_text.splitlines():

            line = line.strip()

            if not line:
                continue

            if line.lower().startswith("table:"):

                current_table = line.split(":")[1].strip()

                self.tables[current_table] = []

            elif line.startswith("-"):

                column = line.replace("-", "").strip()

                self.tables[current_table].append(column)

                # Build normalized lookup
                self.column_lookup[self.normalize(column)] = column

    # -------------------------------------
    # Validate SQL
    # -------------------------------------

    def validate(self, sql):

        sql_lower = sql.lower()

        # -----------------------------
        # Only SELECT
        # -----------------------------

        if not sql_lower.strip().startswith("select"):

            return {
                "score": 0,
                "decision": "FAIL",
                "reason": "Only SELECT statements are allowed.",
                "retry": True,
            }

        # -----------------------------
        # Block dangerous SQL
        # -----------------------------

        for word in self.BLOCKED:

            if re.search(rf"\b{word}\b", sql_lower):

                return {
                    "score": 0,
                    "decision": "FAIL",
                    "reason": f"Blocked SQL command: {word}",
                    "retry": True,
                }

        # -----------------------------
        # Check tables
        # -----------------------------

        tables = re.findall(r"(?:from|join)\s+([a-zA-Z0-9_`]+)", sql_lower)

        allowed_tables = {t.lower() for t in self.tables.keys()}

        for table in tables:

            table = table.replace("`", "")

            if table not in allowed_tables:

                return {
                    "score": 30,
                    "decision": "FAIL",
                    "reason": f"Unknown table: {table}",
                    "retry": True,
                }

        return {
            "score": 100,
            "decision": "PASS",
            "reason": "SQL Valid",
            "retry": False,
        }
