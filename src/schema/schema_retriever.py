from src.schema.schema_loader import SchemaLoader
from src.memory.business_dictionary import BUSINESS_TERMS


class SchemaRetriever:

    def __init__(self):
        self.loader = SchemaLoader()

    def retrieve(self, question: str):

        question = question.lower()

        tables = self.loader.get_schema()

        relevant_schema = []

        for table, columns in tables.items():

            score = 0

            # Table name match
            if table.lower() in question:
                score += 5

            matched_columns = []

            for col in columns:

                col_lower = col.lower()

                # Direct column match
                if col_lower in question:
                    matched_columns.append(col)
                    score += 2

                # Business synonym match
                for word, synonyms in BUSINESS_TERMS.items():

                    if word == col_lower:

                        if any(s in question for s in synonyms):
                            matched_columns.append(col)
                            score += 2

            if score > 0:

                relevant_schema.append(
                    {
                        "table": table,
                        "columns": list(set(matched_columns)),
                        "score": score
                    }
                )

        relevant_schema.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        return relevant_schema
