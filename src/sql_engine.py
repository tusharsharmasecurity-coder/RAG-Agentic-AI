import re
import time
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

print("MemoryManager imported from:", MemoryManager.__module__)
print("MemoryManager methods:", dir(MemoryManager))


class SQLEngine:

    def __init__(self):

        self.confidence = ConfidenceEngine()
        self.db = Database()
        self.memory = MemoryManager()
        self.learner = LearningEngine()
        self.router = ModelRouter()
        self.evaluator = SelfEvaluator()

        # Full database schema
        self.schema_text = self.get_schema()

        # SQL Validator
        self.validator = SQLValidator(self.schema_text)

        # Schema Retriever
        self.schema = SchemaRetriever()

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

        schema = self.build_schema_prompt(question)

        prompt = SQL_SYSTEM_PROMPT.format(schema=schema, question=question)

        response = self.router.sql().invoke(prompt)

        sql = response.content.strip()
        sql = re.sub(r"```sql|```", "", sql).strip()

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

    # ---------------------------------
    # Ask
    # ---------------------------------

    def ask(self, question):

        original_question = question
        question = normalize(question)

        print("\n========== NORMALIZER ==========")
        print("Original :", original_question)
        print("Normalized :", question)

        sql = self.memory.search(question)

        # -----------------------------
        # MEMORY / SQL GENERATION
        # -----------------------------

        if sql:

            print("🧠 Memory Hit")

            evaluation = self.evaluator.evaluate(question, sql)

        else:

            print("🤖 Generating SQL")
            log("SQL_ENGINE", "Generating SQL")

            sql = self.generate_sql(question)

            evaluation = self.evaluator.evaluate(question, sql)

            print("\n========== SELF EVALUATION ==========")
            print(evaluation)

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

        valid = validation["decision"] == "PASS"

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

        MAX_RETRY = 3
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
        # VALIDATION FAILED
        # -----------------------------

        if validation["decision"] == "FAIL":

            return {
                "type": "error",
                "message": validation["reason"],
            }

        # -----------------------------
        # EXECUTE SQL
        # -----------------------------

        try:

            log("SQL_ENGINE", "Executing SQL")

            result = self.execute_sql(sql)

        except Exception as e:

            return {
                "type": "error",
                "message": str(e),
            }

        # -----------------------------
        # SAVE MEMORY
        # -----------------------------

        self.memory.save_sql(
            question=question,
            sql=sql,
            execution_time=result["time"],
        )

        rows = result["rows"]

        if len(rows) <= 20:
            answer = self.result_generator.generate(question, rows)
        else:
            answer = f"Found {len(rows)} records."

        result["answer"] = answer

        log_id = self.learner.save(
            question=original_question,
            normalized_question=question,
            intent="SQL",
            generated_sql=sql,
            final_sql=sql,
            answer=answer,
            success=True,
            execution_time=result["time"],
            model="llama3",
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

        return sql
