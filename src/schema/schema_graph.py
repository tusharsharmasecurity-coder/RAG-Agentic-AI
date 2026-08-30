"""Schema relationships used to expand relevant tables without inventing FKs."""

from __future__ import annotations

from typing import Mapping
import networkx as nx


class SchemaGraph:
    def __init__(self, schema: Mapping[str, list[str]], foreign_keys: Mapping[str, list[dict]] | None = None):
        self.graph = nx.Graph()
        for table, columns in schema.items():
            table_node = f"table:{table}"
            self.graph.add_node(table_node, kind="table", table=table)
            for column in columns:
                column_node = f"column:{table}.{column}"
                self.graph.add_node(column_node, kind="column", table=table, column=column)
                self.graph.add_edge(table_node, column_node, relationship="contains")
        for table, keys in (foreign_keys or {}).items():
            for key in keys:
                target_table = key.get("referred_table")
                if target_table in schema:
                    self.graph.add_edge(f"table:{table}", f"table:{target_table}", relationship="foreign_key")
        awb_tables = [table for table, columns in schema.items() if any(c.lower() == "awb" for c in columns)]
        for index, table in enumerate(awb_tables):
            for other in awb_tables[index + 1:]:
                self.graph.add_edge(f"table:{table}", f"table:{other}", relationship="inferred_awb")

    def related_tables(self, table: str) -> list[str]:
        node = f"table:{table}"
        if node not in self.graph:
            return []
        return [self.graph.nodes[item]["table"] for item in self.graph.neighbors(node) if self.graph.nodes[item]["kind"] == "table"]
