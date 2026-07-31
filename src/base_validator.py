class BaseValidator:

    def validate(self, *args, **kwargs):
        raise NotImplementedError

    def pass_result(self, score=100, reason="OK"):
        return {
            "score": score,
            "decision": "PASS",
            "reason": reason,
            "retry": False,
        }

    def fail_result(self, score=0, reason="Validation Failed"):
        return {
            "score": score,
            "decision": "FAIL",
            "reason": reason,
            "retry": True,
        }