from sqlalchemy import inspect


class SchemaValidator:

    def __init__(self, engine):
        self.engine = engine
        self.inspector = inspect(engine)

    def get_columns(self, table_name):

        columns = self.inspector.get_columns(table_name)

        return [c["name"] for c in columns]

    def validate(self, dataframe, table_name):

        if not self.inspector.has_table(table_name):
            return True, {}

        db_columns = set(self.get_columns(table_name))
        excel_columns = set(dataframe.columns)

        missing = db_columns - excel_columns
        extra = excel_columns - db_columns

        return len(missing) == 0, {
            "missing": list(missing),
            "extra": list(extra)
        }
    def compare(self, excel_columns, db_columns):

        excel = set(col.lower() for col in excel_columns)
        db = set(col.lower() for col in db_columns)

        common = len(excel & db)
        total = max(len(excel), len(db))

        return round((common / total) * 100)