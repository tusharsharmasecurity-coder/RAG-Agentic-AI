from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from rapidfuzz import fuzz, process

from src.entities.entity_registry import EntityRegistry


@dataclass(frozen=True)
class EntityResolutionConfig:
    fuzzy_threshold: float = 90.0
    ambiguity_delta: float = 3.0


class EntityResolver:
    """Resolve entities with exact, alias, fuzzy, ambiguity, and no-match paths."""

    def __init__(self, config: EntityResolutionConfig | None = None):
        self.config = config or EntityResolutionConfig()

    def resolve(
        self,
        value: str,
        candidates: Iterable[str],
        aliases: dict[str, str] | None = None,
    ) -> dict[str, object]:
        normalized_input = EntityRegistry.normalize(value or "")
        candidate_map = {
            EntityRegistry.normalize(candidate): candidate
            for candidate in candidates
            if EntityRegistry.normalize(candidate)
        }

        if not normalized_input:
            return self._result(value, None, 0.0, "none")

        if normalized_input in candidate_map:
            return self._result(value, candidate_map[normalized_input], 100.0, "exact")

        alias_match = (aliases or {}).get(normalized_input)
        if alias_match:
            return self._result(value, alias_match, 100.0, "alias")

        matches = process.extract(
            normalized_input,
            candidate_map.keys(),
            scorer=fuzz.WRatio,
            limit=2,
        )
        if not matches or matches[0][1] < self.config.fuzzy_threshold:
            return self._result(value, None, matches[0][1] if matches else 0.0, "none")

        best_key, best_score, _ = matches[0]
        if len(matches) > 1 and best_score - matches[1][1] <= self.config.ambiguity_delta:
            return self._result(
                value,
                None,
                best_score,
                "ambiguous",
                ambiguous=True,
                candidates=[
                    candidate_map[best_key],
                    candidate_map[matches[1][0]],
                ],
            )

        return self._result(value, candidate_map[best_key], best_score, "fuzzy")

    def resolve_registered(
        self,
        value: str,
        registry: EntityRegistry,
        entity_type: str,
    ) -> dict[str, object]:
        return self.resolve(
            value,
            registry.candidates(entity_type),
            registry.aliases(entity_type),
        )

    @staticmethod
    def _result(
        value: str,
        match: str | None,
        score: float,
        method: str,
        ambiguous: bool = False,
        candidates: list[str] | None = None,
    ) -> dict[str, object]:
        return {
            "input": value,
            "match": match,
            "score": round(float(score), 2),
            "method": method,
            "ambiguous": ambiguous,
            "candidates": candidates or [],
        }
