"""Conservative controlled-vocabulary resolution for logistics terminology."""

import re
from dataclasses import dataclass

from rapidfuzz import fuzz, process


@dataclass(frozen=True)
class EntityMatch:
    value: str | None
    confidence: float
    strategy: str


class EntityResolver:

    def __init__(
        self,
        vocabulary: dict[str, str],
        threshold: float = 94.0,
    ):

        self.vocabulary = {
            key.lower(): value
            for key, value in vocabulary.items()
        }

        self.threshold = threshold

    # =========================================================
    # NORMALIZE TOKEN
    # =========================================================

    @staticmethod
    def _normalize(text: str) -> str:

        text = re.sub(
            r"\s+",
            " ",
            text.lower(),
        ).strip()

        return text

    # =========================================================
    # RESOLVE
    # =========================================================

    def resolve(self, text: str) -> EntityMatch:

        normalized = self._normalize(text)

        if not normalized:

            return EntityMatch(
                None,
                0.0,
                "unresolved",
            )

        # -----------------------------------------------------
        # EXACT MATCH
        # -----------------------------------------------------

        if normalized in self.vocabulary:

            return EntityMatch(
                self.vocabulary[normalized],
                100.0,
                "exact",
            )

        # -----------------------------------------------------
        # NORMALIZED EXACT MATCH
        # -----------------------------------------------------

        compact = re.sub(
            r"[^a-z0-9]",
            "",
            normalized,
        )

        for key, value in self.vocabulary.items():

            compact_key = re.sub(
                r"[^a-z0-9]",
                "",
                key,
            )

            if compact_key == compact:

                return EntityMatch(
                    value,
                    100.0,
                    "normalized",
                )

        # -----------------------------------------------------
        # FUZZY MATCH
        # -----------------------------------------------------

        match = process.extractOne(
            normalized,
            self.vocabulary.keys(),
            scorer=fuzz.ratio,
            score_cutoff=self.threshold,
        )

        if not match:

            return EntityMatch(
                None,
                0.0,
                "unresolved",
            )

        key, score, _ = match

        # -----------------------------------------------------
        # EXTRA SAFETY
        # -----------------------------------------------------
        #
        # Only allow fuzzy correction when the candidate
        # is genuinely close to the input.
        #
        # This protects words such as:
        #
        # status
        # shipment
        # validation
        #
        # from being incorrectly converted into each other.
        # -----------------------------------------------------

        if float(score) < self.threshold:

            return EntityMatch(
                None,
                float(score),
                "unresolved",
            )

        return EntityMatch(
            self.vocabulary[key],
            float(score),
            "fuzzy",
        )