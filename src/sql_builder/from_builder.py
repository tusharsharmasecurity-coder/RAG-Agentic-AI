from src.schema.schema_loader import SchemaLoader


class TableResolutionError(ValueError):
    """Raised when schema metadata cannot satisfy a requested column set."""


class FromBuilder:
    """Build a FROM clause from the existing database schema metadata."""

    def __init__(self, schema_loader=None):
        self.schema_loader = schema_loader or SchemaLoader()

    @staticmethod
    def _quote_identifier(identifier):
        return f"`{identifier.replace('`', '``')}`"

    def resolve_table(self, columns):
        requested_columns = {column.lower() for column in columns}

        for table, available_columns in self.schema_loader.get_schema().items():
            available = {column.lower() for column in available_columns}
            if requested_columns.issubset(available):
                return table

        return None

    def build(self, columns):
        table = self.resolve_table(columns)

        if table is None:
            requested = ", ".join(columns)
            raise TableResolutionError(
                f"No schema table contains all required columns: {requested}"
            )

        return f"FROM {self._quote_identifier(table)}"
