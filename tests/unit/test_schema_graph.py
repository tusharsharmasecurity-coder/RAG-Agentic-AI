from src.schema.schema_graph import SchemaGraph


def test_awb_relationship_is_inferred_but_distinct_from_foreign_key():
    graph = SchemaGraph({"ajio": ["AWB", "Value"], "purple": ["AWB"], "recovry": ["Value"]})
    assert "purple" in graph.related_tables("ajio")
    assert graph.graph.edges["table:ajio", "table:purple"]["relationship"] == "inferred_awb"
