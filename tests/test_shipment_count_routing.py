import unittest

from src.nl2sql.parser import QuestionParser
from src.question_normalizer import QuestionNormalizer
from src.sql_builder.builder import SQLBuilder
from src.sql_builder.from_builder import TableResolutionError


class FakeSchemaLoader:
    def get_schema(self):
        return {
            "shipments": ["AWB", "DC", "Closure"],
            "other_data": ["Value"],
        }


class ShipmentCountRoutingTests(unittest.TestCase):
    def setUp(self):
        self.parser = QuestionParser()
        self.builder = SQLBuilder(schema_loader=FakeSchemaLoader())

    def assert_shipment_count(self, question):
        parsed = self.parser.parse(question)

        self.assertEqual(parsed["intent"], "count")
        self.assertEqual(parsed["metrics"], ["AWB"])
        self.assertEqual(
            self.builder.build(parsed),
            "SELECT COUNT(DISTINCT `AWB`) AS `Total_AWB` FROM `shipments`",
        )

    def test_how_many_shipments(self):
        self.assert_shipment_count("How many shipments?")

    def test_abbreviated_shipment_count(self):
        self.assert_shipment_count("hw mny shipmnt")

    def test_singular_shipment_count(self):
        self.assert_shipment_count("how many shipment")

    def test_total_awb(self):
        self.assert_shipment_count("total AWB")

    def test_missing_schema_column_fails_before_sql_generation(self):
        with self.assertRaisesRegex(TableResolutionError, "No schema table contains"):
            self.builder.build({"intent": "count", "metrics": ["Missing"]})

    def test_both_question_uses_sql_and_rag_portions(self):
        parts = QuestionNormalizer().split(
            "Show shipments affected by closure policy"
        )

        self.assertEqual(parts["sql"], "Show shipments affected by")
        self.assertEqual(parts["rag"], "closure policy")

        parsed = self.parser.parse(parts["sql"])
        self.assertEqual(parsed["metrics"], ["AWB"])
        self.assertEqual(
            self.builder.build(parsed),
            "SELECT `AWB` FROM `shipments`",
        )

    def test_select_resolves_one_table_for_all_requested_columns(self):
        self.assertEqual(
            self.builder.build(
                {"intent": "select", "metrics": ["AWB", "Closure"]}
            ),
            "SELECT `AWB`, `Closure` FROM `shipments`",
        )


if __name__ == "__main__":
    unittest.main()
