from src.schema.schema_loader import SchemaLoader
from src.memory.business_dictionary import BUSINESS_TERMS
from src.cache import CacheManager
from src.schema.schema_graph import SchemaGraph
import hashlib


class SchemaRetriever:

    def __init__(self):
        self.loader = SchemaLoader()
        self.cache = CacheManager()

    def retrieve(self, question: str):

        question = question.lower()
        cache_key = "schema-retrieval:" + hashlib.sha256(question.encode()).hexdigest()
        cached = self.cache.get_json(cache_key)
        if cached is not None:
            return cached

        tables = self.loader.get_schema()
        graph = SchemaGraph(tables, self.loader.get_foreign_keys())

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

                # Business term match; values are canonical database concepts.
                for word, canonical in BUSINESS_TERMS.items():
                    if canonical.lower() == col_lower and word in question:
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

        # Include directly related tables only when a table is already relevant.
        known = {item["table"] for item in relevant_schema}
        for item in list(relevant_schema):
            for related in graph.related_tables(item["table"]):
                if related not in known:
                    relevant_schema.append({"table": related, "columns": tables[related], "score": 0, "relationship": "schema"})
                    known.add(related)

        self.cache.set_json(cache_key, relevant_schema)

        return relevant_schema
