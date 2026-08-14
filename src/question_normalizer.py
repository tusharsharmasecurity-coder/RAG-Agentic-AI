import re


class QuestionNormalizer:
    RAG_TERMS = ("sop", "policy", "guideline", "guidelines", "process", "manual", "documentation")
    SQL_FILLER = {"by", "for", "of", "the", "a", "an"}

    def split(self, question):
        text = question.strip()

        if re.search(r"\band\b", text, flags=re.IGNORECASE):
            sql_question, rag_question = re.split(
                r"\band\b", text, maxsplit=1, flags=re.IGNORECASE
            )
            return {
                "sql": sql_question.strip(),
                "rag": rag_question.strip(),
            }

        rag_match = re.search(
            rf"\b(?:{'|'.join(self.RAG_TERMS)})\b",
            text,
            flags=re.IGNORECASE,
        )

        if rag_match:
            sql_prefix = text[:rag_match.start()].strip()
            rag_question = text[rag_match.start():].strip()
            prefix_words = sql_prefix.split()

            if prefix_words and prefix_words[-1].lower() not in self.SQL_FILLER:
                qualifier = prefix_words.pop()
                rag_question = f"{qualifier} {rag_question}"

            return {
                "sql": " ".join(prefix_words).strip(),
                "rag": rag_question,
            }

        return {
            "sql": text,
            "rag": "",
        }
