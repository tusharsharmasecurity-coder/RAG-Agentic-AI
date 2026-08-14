from sqlalchemy import inspect
from src.db_engine import engine


class SchemaLoader:

    def __init__(self):

        self.inspector = inspect(engine)

    # -----------------------------
    # Return all tables + columns
    # -----------------------------

    def get_schema(self):

        schema = {}

        tables = self.inspector.get_table_names()

        for table in tables:

            columns = self.inspector.get_columns(table)

            schema[table] = [

                column["name"]

                for column in columns

            ]

        return schema

    def get_schema_details(self):
        details = {}

        for table in self.inspector.get_table_names():
            columns = self.inspector.get_columns(table)
            foreign_keys = self.inspector.get_foreign_keys(table)
            primary_key = self.inspector.get_pk_constraint(table).get(
                "constrained_columns",
                [],
            )

            details[table] = {
                "columns": {
                    column["name"]: str(column["type"])
                    for column in columns
                },
                "primary_key": primary_key,
                "foreign_keys": foreign_keys,
            }

        return details

    # -----------------------------
    # Pretty print (debug)
    # -----------------------------

    def print_schema(self):

        schema = self.get_schema()

        for table, columns in schema.items():

            print(f"\nTable: {table}")

            for col in columns:

                print(f" - {col}")
