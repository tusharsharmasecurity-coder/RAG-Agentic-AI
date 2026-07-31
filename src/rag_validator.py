from .base_validator import BaseValidator


class RAGValidator(BaseValidator):

    def validate(self, documents):

        if not documents:

            return self.fail_result(0, "No documents retrieved.")

        if len(documents) < 2:

            return self.fail_result(40, "Low confidence retrieval.")

        return self.pass_result(100, "Relevant documents found.")
