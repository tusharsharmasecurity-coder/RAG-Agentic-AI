import unittest

from src.schema.schema_graph import SchemaGraph
from src.schema.schema_loader import SchemaLoader


class SchemaGraphTests(unittest.TestCase):
    schema = {
        "ajio": {
            "columns": {"AWB": "BIGINT", "DC": "TEXT"},
            "primary_key": [],
            "foreign_keys": [],
        },
        "purple": {
            "columns": {"AWB": "TEXT", "Dispatch Center": "TEXT"},
            "primary_key": [],
            "foreign_keys": [],
        },
        "route_memory": {
            "columns": {"id": "BIGINT", "intent": "VARCHAR"},
            "primary_key": ["id"],
            "foreign_keys": [],
        },
    }

    def test_graph_creation_and_table_nodes(self):
        graph = SchemaGraph.from_schema(self.schema)

        self.assertEqual(set(graph.graph.nodes), set(self.schema))
        self.assertEqual(graph.graph.nodes["ajio"]["source"], "schema_loader")

    def test_column_metadata_is_retained(self):
        graph = SchemaGraph.from_schema(self.schema)

        self.assertEqual(graph.graph.nodes["purple"]["columns"]["AWB"], "TEXT")

    def test_explicit_relationship_is_confirmed(self):
        graph = SchemaGraph.from_schema(
            self.schema,
            explicit_relationships=[
                {
                    "source": "ajio",
                    "target": "route_memory",
                    "evidence": "configured test metadata",
                }
            ],
        )

        relation = graph.graph.edges["ajio", "route_memory"]
        self.assertEqual(relation["relationship_type"], "confirmed")
        self.assertEqual(relation["confidence"], 1.0)

    def test_shared_identifier_relationship_is_labeled_inferred(self):
        graph = SchemaGraph.from_schema(self.schema)

        relation = graph.graph.edges["ajio", "purple"]
        self.assertEqual(relation["relationship_type"], "inferred")
        self.assertIn("awb", relation["evidence"])

    def test_unknown_relationship_is_not_invented(self):
        graph = SchemaGraph.from_schema(self.schema)

        self.assertFalse(graph.graph.has_edge("ajio", "route_memory"))

    def test_path_finding(self):
        graph = SchemaGraph.from_schema(self.schema)

        self.assertEqual(graph.find_path("ajio", "purple"), ["ajio", "purple"])
        self.assertEqual(graph.find_path("ajio", "route_memory"), [])

    def test_relevant_table_ranking_uses_relationship_context(self):
        graph = SchemaGraph.from_schema(self.schema)

        ranked = graph.rank_tables([{"table": "ajio", "columns": ["AWB"], "score": 4}])

        self.assertEqual(ranked[0]["table"], "ajio")
        self.assertEqual(ranked[1]["table"], "purple")
        self.assertEqual(ranked[1]["relationship_context"]["relationship_type"], "inferred")

    def test_empty_and_invalid_schema_are_safe(self):
        self.assertEqual(len(SchemaGraph.from_schema({}).graph.nodes), 0)
        graph = SchemaGraph.from_schema({"invalid": {}})
        self.assertEqual(graph.graph.nodes["invalid"]["columns"], {})

    def test_real_schema_has_nodes_and_no_confirmed_relationships(self):
        graph = SchemaGraph.from_loader(SchemaLoader())

        self.assertIn("ajio", graph.graph.nodes)
        self.assertIn("AWB", graph.graph.nodes["ajio"]["columns"])
        self.assertFalse(
            any(
                data["relationship_type"] == "confirmed"
                for _, _, data in graph.graph.edges(data=True)
            )
        )


if __name__ == "__main__":
    unittest.main()
