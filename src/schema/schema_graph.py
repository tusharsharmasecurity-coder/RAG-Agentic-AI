from __future__ import annotations

import re
from typing import Any

import networkx as nx

from src.schema.schema_loader import SchemaLoader


class SchemaGraph:
    """Evidence-aware table relationship graph built from schema metadata."""

    IDENTIFIER_COLUMNS = {"awb", "waybill", "wbn", "shipmentid", "orderid"}
    INFERRED_CONFIDENCE = 0.65

    def __init__(self, graph: nx.Graph | None = None):
        self.graph = graph or nx.Graph()

    @classmethod
    def from_loader(cls, loader: SchemaLoader | None = None) -> "SchemaGraph":
        return cls.from_schema((loader or SchemaLoader()).get_schema_details())

    @classmethod
    def from_schema(
        cls,
        schema: dict[str, dict[str, Any]],
        explicit_relationships: list[dict[str, Any]] | None = None,
    ) -> "SchemaGraph":
        instance = cls()

        for table, metadata in schema.items():
            columns = metadata.get("columns", {}) if isinstance(metadata, dict) else {}
            instance.graph.add_node(
                table,
                columns=dict(columns),
                primary_key=list(metadata.get("primary_key", [])),
                source="schema_loader",
            )

        instance._add_foreign_key_edges(schema)
        instance._add_explicit_edges(explicit_relationships or [])
        instance._add_identifier_inferences(schema)
        return instance

    def _add_foreign_key_edges(self, schema: dict[str, dict[str, Any]]) -> None:
        for table, metadata in schema.items():
            for foreign_key in metadata.get("foreign_keys", []):
                target = foreign_key.get("referred_table")
                if target and target in self.graph:
                    self.graph.add_edge(
                        table,
                        target,
                        relationship_type="confirmed",
                        evidence="database foreign key",
                        confidence=1.0,
                    )

    def _add_explicit_edges(self, relationships: list[dict[str, Any]]) -> None:
        for relationship in relationships:
            source = relationship.get("source")
            target = relationship.get("target")
            if source not in self.graph or target not in self.graph:
                continue
            self.graph.add_edge(
                source,
                target,
                relationship_type="confirmed",
                evidence=relationship.get("evidence", "explicit metadata"),
                confidence=relationship.get("confidence", 1.0),
            )

    def _add_identifier_inferences(self, schema: dict[str, dict[str, Any]]) -> None:
        tables = list(schema)
        for index, source in enumerate(tables):
            source_columns = self._identifier_columns(schema[source])
            for target in tables[index + 1:]:
                if self.graph.has_edge(source, target):
                    continue

                shared = source_columns & self._identifier_columns(schema[target])
                if shared:
                    self.graph.add_edge(
                        source,
                        target,
                        relationship_type="inferred",
                        evidence=f"shared identifier column(s): {', '.join(sorted(shared))}",
                        confidence=self.INFERRED_CONFIDENCE,
                    )

    def related_tables(self, table: str) -> list[dict[str, Any]]:
        if table not in self.graph:
            return []
        return [
            {"table": neighbor, **self.graph.edges[table, neighbor]}
            for neighbor in sorted(self.graph.neighbors(table))
        ]

    def find_path(self, source: str, target: str) -> list[str]:
        if source not in self.graph or target not in self.graph:
            return []
        try:
            return nx.shortest_path(self.graph, source, target)
        except nx.NetworkXNoPath:
            return []

    def rank_tables(self, direct_matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
        ranked = {item["table"]: dict(item) for item in direct_matches}

        for item in direct_matches:
            for relation in self.related_tables(item["table"]):
                neighbor = relation["table"]
                if neighbor in ranked:
                    continue
                ranked[neighbor] = {
                    "table": neighbor,
                    "columns": [],
                    "score": round(item["score"] * relation["confidence"], 2),
                    "relationship_context": relation,
                }

        return sorted(ranked.values(), key=lambda item: item["score"], reverse=True)

    def enrich(self, direct_matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for item in direct_matches:
            item["related_tables"] = self.related_tables(item["table"])
        return direct_matches

    @classmethod
    def _identifier_columns(cls, metadata: dict[str, Any]) -> set[str]:
        return {
            cls._normalize(column)
            for column in metadata.get("columns", {})
            if cls._normalize(column) in cls.IDENTIFIER_COLUMNS
        }

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"[^a-z0-9]", "", value.lower())
