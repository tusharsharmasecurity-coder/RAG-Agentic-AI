import unittest

from sqlglot import exp

from src.database import Database
from src.sql.sqlglot_validator import SQLGlotValidator


class SQLGlotValidatorTests(unittest.TestCase):
    def setUp(self):
        self.validator = SQLGlotValidator(dialect="mysql")

    def test_count_query_is_parsed_as_select(self):
        result = self.validator.validate("SELECT COUNT(*) FROM shipments;")

        self.assertTrue(result["valid"])
        self.assertEqual(result["statement_type"], "SELECT")
        self.assertIsInstance(result["ast"], exp.Select)

    def test_revenue_sum_is_valid_syntax(self):
        result = self.validator.validate("SELECT SUM(revenue) FROM shipments;")

        self.assertTrue(result["valid"])

    def test_awb_sum_is_a_business_rule_violation(self):
        result = self.validator.validate("SELECT SUM(AWB) FROM shipments;")

        self.assertFalse(result["valid"])
        self.assertIn("AWB is an identifier", result["reason"])

    def test_prohibited_write_statements_are_blocked(self):
        statements = (
            "DROP TABLE shipments;",
            "DELETE FROM shipments;",
            "UPDATE shipments SET status = 'Delivered';",
            "TRUNCATE TABLE shipments;",
        )

        for statement in statements:
            with self.subTest(statement=statement):
                result = self.validator.validate(statement)
                self.assertFalse(result["valid"])
                self.assertIn("Prohibited", result["reason"])

    def test_invalid_sql_is_rejected(self):
        result = self.validator.validate("SELECT ( FROM ajio;")

        self.assertFalse(result["valid"])
        self.assertIn("parse failure", result["reason"].lower())

    def test_grouped_analytical_query_is_valid(self):
        result = self.validator.validate(
            "SELECT DC, COUNT(*) FROM ajio GROUP BY DC;"
        )

        self.assertTrue(result["valid"])
        self.assertEqual(result["statement_type"], "SELECT")

    def test_real_read_only_aggregate_against_company_schema(self):
        sql = "SELECT COUNT(*) AS shipment_count FROM ajio;"
        result = self.validator.validate(sql)

        self.assertTrue(result["valid"])
        db = Database()
        try:
            db.cursor.execute(result["sql"])
            row = db.cursor.fetchone()
        finally:
            db.close()

        self.assertIsInstance(row[0], int)


if __name__ == "__main__":
    unittest.main()
