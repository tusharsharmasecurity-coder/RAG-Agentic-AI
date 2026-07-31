from sqlalchemy import inspect
from src.db_engine import engine


class ExcelImporter:

    def __init__(self):
        self.engine = engine

    def table_exists(self, table_name):
        inspector = inspect(self.engine)
        return inspector.has_table(table_name)

    def import_excel(self, df, table_name, mode):

    # Import Excel into MySQL
     print("=" * 60)
     print("Columns received by ExcelImporter:")
     print(df.columns.tolist())
     print("=" * 60)
     df.to_sql(
        table_name,
        self.engine,
        if_exists=mode,
        index=False
    )

    # Mark this table as the active dataset
     with self.engine.begin() as conn:

        conn.exec_driver_sql(
            """
            UPDATE system_settings
            SET setting_value = %s
            WHERE setting_key = 'active_table'
            """,
            (table_name,)
        )

     return len(df)