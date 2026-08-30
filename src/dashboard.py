import logging

logger = logging.getLogger(__name__)


class Dashboard:
    # ... your existing code ...

    def close(self):
        """Safely close dashboard resources."""
        pass
    
    def __init__(self, db):
        self.db = db

    def get_active_table(self):
        result = self.db.execute_one(
            """
            SELECT setting_value
            FROM system_settings
            WHERE setting_key = 'active_table'
            """
        )

        if not result:
            return None

        return result[0]

    def get_stats(self):
        """
        Return dashboard statistics using the currently active table.

        The application currently uses tataunystore rather than a
        hard-coded shipments table.
        """

        active_table = self.get_active_table()

        if not active_table:
            return {
                "shipments": 0,
                "delayed": 0,
                "delivered": 0,
                "tables": 0,
            }

        # Basic protection against SQL injection through the table name.
        if not active_table.replace("_", "").isalnum():
            raise ValueError(f"Invalid active table name: {active_table}")

        # Number of tables in the database.
        tables_result = self.db.execute_one(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            """
        )

        tables = tables_result[0] if tables_result else 0

        # Total records in active table.
        shipments_result = self.db.execute_one(
            f"SELECT COUNT(*) FROM `{active_table}`"
        )

        shipments = shipments_result[0] if shipments_result else 0

        return {
            "shipments": shipments,
            "delayed": 0,
            "delivered": 0,
            "tables": tables,
        }