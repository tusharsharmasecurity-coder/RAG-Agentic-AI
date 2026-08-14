class ConfidenceGate:
    """Accept routing decisions only when their confidence meets the threshold."""

    def __init__(self, threshold: float = 0.80):
        self.threshold = threshold

    def allows(self, route_result: dict | None) -> bool:
        if not route_result:
            return False

        confidence = route_result.get("score")
        return isinstance(confidence, (int, float)) and confidence >= self.threshold
