class QuestionNormalizer:

    def split(self, question):

        text = question.lower()

        if " and " in text:

            parts = question.split(" and ", 1)

            return {
                "sql": parts[0].strip(),
                "rag": parts[1].strip()
            }

        return {
            "sql": question,
            "rag": ""
        }