from src.entity_resolver import EntityResolver
from src.memory.business_dictionary import BUSINESS_TERMS


def test_entity_resolution_prefers_exact_then_fuzzy():
    resolver = EntityResolver(BUSINESS_TERMS)
    assert resolver.resolve("warehouse").strategy == "exact"
    fuzzy = resolver.resolve("warehous")
    assert fuzzy.value == "DC"
    assert fuzzy.strategy == "fuzzy"


def test_low_confidence_entity_is_unresolved():
    result = EntityResolver(BUSINESS_TERMS).resolve("unrelatedterm")
    assert result.strategy == "unresolved"
    assert result.value is None
