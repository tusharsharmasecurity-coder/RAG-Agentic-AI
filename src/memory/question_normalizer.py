import re

from src.memory.business_dictionary import BUSINESS_TERMS


def normalize(question: str) -> str:
    """
    Normalize questions for semantic memory lookup.

    This normalization preserves natural-language meaning while
    canonicalizing known business terminology.
    """

    if not question:
        return ""

    question = re.sub(
        r"\s+",
        " ",
        question,
    ).strip().lower()

    # Remove punctuation
    question = re.sub(
        r"[^a-z0-9 ]",
        " ",
        question,
    )

    question = re.sub(
        r"\s+",
        " ",
        question,
    ).strip()

    # Normalize business terminology
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

    return question