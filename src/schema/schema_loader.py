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

    # -----------------------------
    # Pretty print (debug)
    # -----------------------------

    def print_schema(self):

        schema = self.get_schema()

        for table, columns in schema.items():

            print(f"\nTable: {table}")

            for col in columns:

                print(f" - {col}")