import re

from src.memory.business_dictionary import BUSINESS_TERMS
from src.entity_resolver import EntityResolver


RESOLVER = EntityResolver(BUSINESS_TERMS)


def normalize(question: str) -> str:
    """
    Normalize a user question without destroying its semantic structure.

    Rules:
    - Preserve the original meaning and sentence structure.
    - Normalize business terms.
    - Apply controlled fuzzy correction only to individual words.
    - Do NOT remove stop words.
    - Do NOT convert a complete natural-language question into keywords.
    """

    if not question:
        return ""

    # Normalize whitespace
    question = re.sub(r"\s+", " ", question).strip().lower()

    # Remove punctuation while preserving word boundaries
    question = re.sub(r"[^a-z0-9 ]", " ", question)

    question = re.sub(r"\s+", " ", question).strip()

    # -------------------------------------------------
    # BUSINESS TERM NORMALIZATION
    # -------------------------------------------------

    for key, value in sorted(
        BUSINESS_TERMS.items(),
        key=lambda x: len(x[0]),
        reverse=True,
    ):
        pattern = r"\b" + re.escape(key.lower()) + r"\b"

        question = re.sub(
            pattern,
            value,
            question,
        )

    # -------------------------------------------------
    # CONTROLLED FUZZY CORRECTION
    # -------------------------------------------------

    words = []

    for word in question.split():

        match = RESOLVER.resolve(word)

        # Only replace when the resolver explicitly
        # identifies the word as a fuzzy match.
        if match.strategy == "fuzzy":
            word = match.value

        words.append(word)

    # -------------------------------------------------
    # FINAL CLEANUP
    # -------------------------------------------------

    normalized = " ".join(words)

    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    ).strip()

    return normalized