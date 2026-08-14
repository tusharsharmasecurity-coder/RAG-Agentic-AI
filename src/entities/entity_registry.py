from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from src.database import Database
from src.memory.business_dictionary import BUSINESS_TERMS
from src.metadata.metadata_store import MetadataStore
from src.schema.schema_loader import SchemaLoader


class EntityRegistry:
    """Candidate and alias registry backed by existing project metadata."""

    CENTER_COLUMNS = {"dc", "dispatch center"}

    def __init__(
        self,
        candidates: dict[str, Iterable[str]] | None = None,
        aliases: dict[str, dict[str, Iterable[str]]] | None = None,
    ):
        self._candidates: dict[str, set[str]] = defaultdict(set)
        self._aliases: dict[str, dict[str, str]] = defaultdict(dict)

        for entity_type, values in (candidates or {}).items():
            self.add_candidates(entity_type, values)

        for entity_type, mappings in (aliases or {}).items():
            for canonical, values in mappings.items():
                self.add_aliases(entity_type, canonical, values)

    @classmethod
    def from_project_metadata(
        cls,
        database: Database | None = None,
        schema_loader: SchemaLoader | None = None,
        candidate_limit: int = 5000,
    ) -> "EntityRegistry":
        registry = cls()
        registry._load_business_aliases()
        registry._load_metadata_aliases()
        registry.refresh_center_candidates(
            database=database,
            schema_loader=schema_loader,
            candidate_limit=candidate_limit,
        )
        return registry

    def add_candidates(self, entity_type: str, values: Iterable[str]) -> None:
        self._candidates[entity_type].update(
            str(value).strip()
            for value in values
            if value is not None and str(value).strip()
        )

    def add_aliases(
        self,
        entity_type: str,
        canonical: str,
        aliases: Iterable[str],
    ) -> None:
        self.add_candidates(entity_type, [canonical])
        for alias in aliases:
            normalized_alias = self.normalize(alias)
            if normalized_alias:
                self._aliases[entity_type][normalized_alias] = canonical

    def candidates(self, entity_type: str) -> list[str]:
        return sorted(self._candidates[entity_type])

    def aliases(self, entity_type: str) -> dict[str, str]:
        return dict(self._aliases[entity_type])

    def refresh_center_candidates(
        self,
        database: Database | None = None,
        schema_loader: SchemaLoader | None = None,
        candidate_limit: int = 5000,
    ) -> None:
        owns_database = database is None
        db = database or Database()
        center_columns = {self.normalize(name) for name in self.CENTER_COLUMNS}

        try:
            schema = (schema_loader or SchemaLoader()).get_schema()

            for table, columns in schema.items():
                for column in columns:
                    if self.normalize(column) not in center_columns:
                        continue

                    identifier = self._quote_identifier(column)
                    table_identifier = self._quote_identifier(table)
                    db.cursor.execute(
                        f"SELECT DISTINCT {identifier} FROM {table_identifier} "
                        f"WHERE {identifier} IS NOT NULL LIMIT %s",
                        (candidate_limit,),
                    )
                    self.add_candidates(
                        "center",
                        (row[0] for row in db.cursor.fetchall()),
                    )
        finally:
            if owns_database:
                db.close()

    def _load_business_aliases(self) -> None:
        aliases = [
            term
            for term, canonical in BUSINESS_TERMS.items()
            if self.normalize(canonical) == self.normalize("DC")
        ]
        self.add_aliases("schema", "DC", aliases)

    def _load_metadata_aliases(self) -> None:
        for item in MetadataStore().load():
            canonical = item.get("entity") or item.get("column")
            entity_type = item.get("entity_type", "schema")
            aliases = item.get("aliases", [])
            if canonical and aliases:
                self.add_aliases(entity_type, canonical, aliases)

    @staticmethod
    def normalize(value: str) -> str:
        return " ".join(
            "".join(character if character.isalnum() else " " for character in value.lower()).split()
        )

    @staticmethod
    def _quote_identifier(identifier: str) -> str:
        return f"`{identifier.replace('`', '``')}`"
