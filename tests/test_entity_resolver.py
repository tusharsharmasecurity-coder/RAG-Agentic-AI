import unittest

from src.entities.entity_registry import EntityRegistry
from src.entities.entity_resolver import EntityResolver, EntityResolutionConfig


class EntityResolverTests(unittest.TestCase):
    def setUp(self):
        self.resolver = EntityResolver(
            EntityResolutionConfig(fuzzy_threshold=90.0, ambiguity_delta=3.0)
        )
        self.registry = EntityRegistry(
            candidates={"schema": ["DC", "Dispatch Center"]},
            aliases={"schema": {"DC": ["warehouse", "hub", "center"]}},
        )

    def test_exact_match(self):
        result = self.resolver.resolve_registered("dc", self.registry, "schema")

        self.assertEqual(result["match"], "DC")
        self.assertEqual(result["method"], "exact")

    def test_alias_match(self):
        result = self.resolver.resolve_registered("warehouse", self.registry, "schema")

        self.assertEqual(result["match"], "DC")
        self.assertEqual(result["method"], "alias")

    def test_fuzzy_match(self):
        result = self.resolver.resolve_registered(
            "Disptch Cnter", self.registry, "schema"
        )

        self.assertEqual(result["match"], "Dispatch Center")
        self.assertEqual(result["method"], "fuzzy")

    def test_low_confidence_is_not_matched(self):
        result = self.resolver.resolve_registered("unrelated", self.registry, "schema")

        self.assertIsNone(result["match"])
        self.assertEqual(result["method"], "none")

    def test_ambiguous_match_is_not_silently_selected(self):
        registry = EntityRegistry(
            candidates={"schema": ["Dispatch Center", "Dispatch Centre"]}
        )

        result = self.resolver.resolve_registered("Dispatch Cente", registry, "schema")

        self.assertIsNone(result["match"])
        self.assertTrue(result["ambiguous"])
        self.assertEqual(result["method"], "ambiguous")

    def test_empty_input(self):
        result = self.resolver.resolve_registered("", self.registry, "schema")

        self.assertIsNone(result["match"])
        self.assertEqual(result["method"], "none")

    def test_case_and_punctuation_normalization(self):
        result = self.resolver.resolve_registered(
            "dispatch-center", self.registry, "schema"
        )

        self.assertEqual(result["match"], "Dispatch Center")
        self.assertEqual(result["method"], "exact")

    def test_real_center_metadata_can_be_resolved_without_exposing_values(self):
        registry = EntityRegistry.from_project_metadata(candidate_limit=5000)
        candidates = registry.candidates("center")

        self.assertGreater(len(candidates), 0)
        result = self.resolver.resolve_registered(candidates[0], registry, "center")

        self.assertEqual(result["method"], "exact")
        self.assertEqual(result["match"], candidates[0])


if __name__ == "__main__":
    unittest.main()
