from .base_validator import BaseValidator

class PlannerValidator(BaseValidator):

    def validate(self, question, intent):

        valid = {
            "SQL",
            "RAG",
            "BOTH",
            "CHAT",
            "DATAFRAME"
        }

        if intent not in valid:
            return self.fail_result(
                0,
                "Unknown intent."
            )

        return self.pass_result()