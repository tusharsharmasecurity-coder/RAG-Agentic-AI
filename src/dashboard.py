from src.database import Database


class Dashboard:

    def __init__(self):

        self.db = Database()

    # --------------------------------------
    # Active Dataset
    # --------------------------------------

    def get_active_table(self):

        result = self.db.execute_one("""
            SELECT setting_value
            FROM system_settings
            WHERE setting_key='active_table'
            """)

        if result:
            return result[0]

        return "No Dataset"

    # --------------------------------------
    # Dashboard KPIs
    # --------------------------------------

    def get_stats(self):

        active_table = self.get_active_table()

        print("Active Table:", active_table)

        if active_table == "No Dataset":

            return {"shipments": 0, "delayed": 0, "delivered": 0, "tables": 0}

        shipments = self.db.execute_one(f"""
            SELECT COUNT(*)
            FROM `{active_table}`
            """)[0]

        tables = self.db.execute_one("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema='delhivery_ai'
            """)[0]

        return {"shipments": shipments, "delayed": 0, "delivered": 0, "tables": tables}
