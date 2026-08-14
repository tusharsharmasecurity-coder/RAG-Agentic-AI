import re
import time
import hashlib
from typing import Any
from src.quality.self_evaluator import SelfEvaluator
from src.logger import log
from src.database import Database
from src.prompt import SQL_SYSTEM_PROMPT
from src.models.router import ModelRouter
from src.memory.memory_manager import MemoryManager
from src.schema.schema_retriever import SchemaRetriever
from src.sql_validator import SQLValidator
from src.result_generator import ResultGenerator
from src.text_normalizer import normalize
from src.learner import LearningEngine
from src.quality.confidence_engine import ConfidenceEngine
from src.nl2sql.nl2sql import NL2SQLEngine
from src.nl2sql.parser import QuestionParser
from src.sql_builder.builder import SQLBuilder
from src.sql_builder.from_builder import TableResolutionError
from src.sql.sqlglot_validator import SQLGlotValidator
from src.cache.cache_manager import CacheManager

print("MemoryManager imported from:", MemoryManager.__module__)
print("MemoryManager methods:", dir(MemoryManager))


class SQLEngine:

    def __init__(self):

        # NL2SQL Components
        self.parser = QuestionParser()
        self.nl2sql = NL2SQLEngine()
        self.builder = SQLBuilder()

        self.db = Database()
        self.cache = CacheManager()
        self.memory = MemoryManager()
        self.learner = LearningEngine()
        self.router = ModelRouter()
        self.evaluator = SelfEvaluator()

        # Full database schema
        self.schema_text = self.get_schema()

        self.validator = SQLValidator(self.schema_text)
        self.sqlglot_validator = SQLGlotValidator()

        self.schema = SchemaRetriever()

        self.confidence = ConfidenceEngine()

        self.result_generator = ResultGenerator()

        log("SQL_ENGINE", "Ready")

    # ---------------------------------
    # Load Full Schema
    # ---------------------------------

    def get_schema(self):

        cursor = self.db.connection.cursor()

        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        schema = ""

        for (table,) in tables:

            schema += f"\nTable: {table}\n"

            cursor.execute(f"SHOW COLUMNS FROM `{table}`")
            columns = cursor.fetchall()

            for column in columns:
                schema += f"- {column[0]}\n"

        cursor.close()

        return schema

    # ---------------------------------
    # Build Relevant Schema
    # ---------------------------------

    def build_schema_prompt(self, question):

        relevant = self.schema.retrieve(question)

        prompt = ""

        for table in relevant:
            prompt += f"\nTable: {table['table']}\n"

            for col in table["columns"]:
                prompt += f"- {col}\n"

        return prompt

    # ---------------------------------
    # Generate SQL
    # ---------------------------------

    def generate_sql(self, question):

        # ----------------------------
        # Parse the natural language
        # ----------------------------

        parsed = self.parser.parse(question)

        print("\n========== NL2SQL PARSER ==========")
        print(parsed)

        # ----------------------------
        # Retrieve relevant schema
        # ----------------------------

        parsed = self.nl2sql.process(question)

        schema = self.build_schema_prompt(parsed["normalized"])

        prompt = SQL_SYSTEM_PROMPT.format(
            schema=schema,
            question=f"""
            Original Question:
            {question}

Parsed Intent:
{parsed["intent"]}

Metrics:
{parsed["metrics"]}

Filters:
{parsed["filters"]}

Group By:
{parsed["group_by"]}

Time:
{parsed["time"]}

Limit:
{parsed["limit"]}

Normalized Question:
{parsed["normalized"]}
""",
        )

        # ----------------------------
        # Previous successful examples
        # ----------------------------

        examples = self.learner.get_similar_examples(question)

        example_text = ""

        for i, (old_question, old_sql) in enumerate(examples, start=1):

            example_text += f"""

Example {i}

Question:
{old_question}

SQL:
{old_sql}

"""

        # ----------------------------
        # Build prompt
        # ----------------------------

        prompt = SQL_SYSTEM_PROMPT.format(
            schema=schema,
            examples=example_text,
            question=question,
            intent=parsed["intent"],
            metrics=", ".join(parsed["metrics"]),
            filters=", ".join(parsed["filters"]),
            group_by=", ".join(parsed["group_by"]),
            time=parsed["time"],
            sort=parsed["sort"],
            limit=parsed["limit"],
        )

        response = self.router.sql().invoke(prompt)

        response_text = response.content.strip()

        match = re.search(
            r"SELECT[\s\S]*?;",
            response_text,
            re.IGNORECASE,
        )

        if match:

            sql = match.group(0)

        else:

            sql = response_text

        print("\n========== GENERATED SQL ==========")
        print(sql)

        return sql

    # ---------------------------------
    # Execute SQL
    # ---------------------------------

    def execute_sql(self, sql):

        cursor = self.db.connection.cursor()

        start = time.time()

        cursor.execute(sql)

        rows = cursor.fetchall()
        columns = [c[0] for c in cursor.description]

        elapsed = round(time.time() - start, 4)

        cursor.close()

        return {
            "type": "table",
            "columns": columns,
            "rows": rows,
            "time": elapsed,
            "sql": sql,
        }

    def _cache_key(self, sql):
        normalized_sql = " ".join(sql.strip().split())

        sql_hash = hashlib.sha256(normalized_sql.encode("utf-8")).hexdigest()

        return f"sql_result:{sql_hash}"

    # ---------------------------------
    # Ask
    # ---------------------------------

    def ask(self, question):

        original_question = question
        question = normalize(question)
        parsed = self.nl2sql.process(question)

        print("\n========== NL2SQL ==========")
        print(parsed)

        question = parsed["normalized"]

        print("\n========== NORMALIZER ==========")
        print("Original :", original_question)
        print("Normalized :", question)

        # -----------------------------
        # MEMORY / SQL GENERATION
        # -----------------------------

        memory = self.memory.search(question)

        if memory:

            print("🧠 Memory Hit")

            print("\n========== MEMORY HIT ==========")
            print("Matched Question :", memory["question"])
            print("Similarity Score :", round(memory["score"], 3))
            print("Previous SQL :")
            print(memory["sql"])

            sql = memory["sql"]

            evaluation = self.evaluator.evaluate(
                question,
                sql,
            )

        else:

            print("Using SQL Builder")

            try:
                sql = self.builder.build(parsed)
            except TableResolutionError as error:
                return {
                    "type": "error",
                    "message": str(error),
                }

            print("\n========== SQL BUILDER ==========")
            print(sql)

            evaluation = {
                "score": 100,
                "reason": "Template SQL",
            }

            if evaluation["score"] < 85:

                print("\n========== RETRY ==========")

                sql = self.retry_sql(
                    question,
                    sql,
                    evaluation["reason"],
                )

                evaluation = self.evaluator.evaluate(question, sql)

        print("\n========== GENERATED SQL ==========")
        print(sql)

        # -----------------------------
        # VALIDATION
        # -----------------------------

        validation = self.validator.validate(sql)

        print("\n========== VALIDATOR ==========")
        print(validation)

        if validation["decision"] == "FAIL":
            return {
                "type": "error",
                "message": validation["reason"],
            }

        sqlglot_validation = self.sqlglot_validator.validate(sql)

        print("\n========== SQLGLOT VALIDATOR ==========")
        print({key: value for key, value in sqlglot_validation.items() if key != "ast"})

        if not sqlglot_validation["valid"]:
            return {
                "type": "error",
                "message": sqlglot_validation["reason"],
            }

        sql = sqlglot_validation["sql"]
        valid = True

        # -----------------------------
        # CONFIDENCE
        # -----------------------------

        confidence = self.confidence.calculate(
            evaluation,
            valid,
        )

        print("\n========== CONFIDENCE ==========")
        print(confidence)

        # -----------------------------
        # LOW CONFIDENCE RETRY
        # -----------------------------

        MAX_RETRY = 2
        retry = 0

        while confidence["score"] < 80 and retry < MAX_RETRY:

            retry += 1

            print(f"\n========== CONFIDENCE RETRY {retry} ==========")

            sql = self.retry_sql(
                question,
                sql,
                "Low confidence score",
            )

            evaluation = self.evaluator.evaluate(question, sql)

            validation = self.validator.validate(sql)

            valid = validation["decision"] == "PASS"

            confidence = self.confidence.calculate(
                evaluation,
                valid,
            )

            print(confidence)

        if confidence["score"] < 80:

            return {
                "type": "error",
                "message": "Unable to generate reliable SQL after multiple retries.",
            }

        # -----------------------------
        # EXECUTE SQL
        # -----------------------------

        try:
            log("SQL_ENGINE", "Checking Redis cache")

            cache_key = self._cache_key(sql)
            cached_result = self.cache.get(cache_key)

            if cached_result is not None:
                log("SQL_ENGINE", "Redis Cache HIT")
            print("\n========== REDIS CACHE HIT ==========")
            return cached_result

            log("SQL_ENGINE", "Redis Cache MISS")
            print("\n========== REDIS CACHE MISS ==========")

            result = self.execute_sql(sql)

            self.cache.set(
                cache_key,
                result,
            )

        except Exception as e:
            return {
                "type": "error",
                "message": str(e),
            }

        except Exception as e:

            return {
                "type": "error",
                "message": str(e),
            }

        # -----------------------------
        # SAVE MEMORY
        # -----------------------------

        rows = result["rows"]

        if len(rows) <= 20:
            start = time.time()
            answer = self.result_generator.generate(question, rows)
            print(f"Result Generator Time: {time.time() - start:.2f} sec")
        else:
            answer = f"Found {len(rows)} records."

        result["answer"] = answer
        start = time.time()
        log_id = self.learner.save(
            question=original_question,
            normalized_question=question,
            user_corrected_question=None,
            intent="SQL",
            generated_sql=sql,
            final_sql=sql,
            corrected_sql=sql,
            answer=answer,
            success=True,
            execution_time=result["time"],
            model="llama3",
            planner_confidence=confidence["score"],
            evaluation_score=evaluation["score"],
        )
        print(f"Learning Save Time: {time.time() - start:.2f} sec")
        self.memory.save_sql(
            question=question,
            sql=sql,
            answer=answer,
            log_id=log_id,
            execution_time=result["time"],
        )
        result["log_id"] = log_id

        return result

    def retry_sql(self, question, previous_sql, reason):

        prompt = f"""
      The previous SQL was rejected.

       User Question:
       {question}

Previous SQL:
{previous_sql}

Reason:
{reason}

Generate a corrected SQL query.

Return ONLY SQL.
"""

        response = self.router.sql().invoke(prompt)

        sql = response.content.strip()

        print("\n========== RETRY SQL ==========")
        print(sql)
        print(NL2SQLEngine)
        print(dir(NL2SQLEngine))
        return sql
