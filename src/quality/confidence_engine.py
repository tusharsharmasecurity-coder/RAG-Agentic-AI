class ConfidenceEngine:

    def calculate(self, evaluation, validator):

        score = evaluation["score"]

        if validator is False:
            score -= 40

        if score >= 95:
            level = "HIGH"

        elif score >= 80:
            level = "MEDIUM"

        else:
            level = "LOW"

        return {
            "score": score,
            "level": level
        }