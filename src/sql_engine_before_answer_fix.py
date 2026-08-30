import os
import re
import time
from typing import Optional, Set
from src.memory.experience_verifier import ExperienceVerifier
import sqlglot
from sqlglot import exp

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
from src.sql_builder import SQLBuilder
from src.sql_optimizer import SQLOptimizer


class SQLEngine:

    def __init__(self):

        self.confidence = ConfidenceEngine()

        self.db = Database()

        self.memory = MemoryManager()
        self.experience_verifier = ExperienceVerifier()

        self.learner = LearningEngine()

        self.router = ModelRouter()

        self.evaluator = SelfEvaluator()

        self.sql_builder = SQLBuilder()

        self.sql_optimizer = SQLOptimizer()

        # Optional expensive LLM self-evaluation.
        # Disabled by default for performance.
        self.enable_self_evaluation = os.getenv(
            "ENABLE_SELF_EVALUATION",
            "false",
        ).lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

        # --------------------------------------------------------
        # Load database schema
        # --------------------------------------------------------

        self.schema_text = self.get_schema()

        # --------------------------------------------------------
        # SQL Validator
        # --------------------------------------------------------

        self.validator = SQLValidator(self.schema_text)

        # --------------------------------------------------------
        # Schema Retriever
        # --------------------------------------------------------

        self.schema = SchemaRetriever()

        self.result_generator = ResultGenerator()

        log(
            "SQL_ENGINE",
            "Ready",
        )

    # ============================================================
    # DATABASE SCHEMA
    # ============================================================

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

    # ============================================================
    # RELEVANT SCHEMA
    # ============================================================

    def build_schema_prompt(
        self,
        question,
    ):

        relevant = self.schema.retrieve(question)

        prompt = ""

        for table in relevant:

            prompt += f"\nTable: " f"{table['table']}\n"

            for column in table["columns"]:

                prompt += f"- {column}\n"

        return prompt

    # ============================================================
    # SQL GENERATION
    # ============================================================

    def generate_sql(
        self,
        question,
    ):

        start = time.time()

        schema = self.build_schema_prompt(question)

        prompt = SQL_SYSTEM_PROMPT.format(
            schema=schema,
            question=question,
        )

        response = self.router.sql().invoke(prompt)

        sql = self.sql_builder.build(response.content)

        sql = self.sql_optimizer.optimize(sql)

        print("\n========== GENERATED SQL ==========")

        print(sql)

        print(f"[TIMING] SQL generation = " f"{time.time() - start:.3f}s")

        return sql

    # ============================================================
    # SQL EXECUTION
    # ============================================================

    def execute_sql(
        self,
        sql,
    ):

        start = time.time()

        cursor = self.db.connection.cursor()

        cursor.execute(sql)

        rows = cursor.fetchall()

        columns = [item[0] for item in cursor.description]

        elapsed = round(
            time.time() - start,
            4,
        )

        cursor.close()

        print(f"[TIMING] MySQL execution = " f"{elapsed:.4f}s")

        return {
            "type": "table",
            "columns": columns,
            "rows": rows,
            "time": elapsed,
            "sql": sql,
        }

    # ============================================================
    # ANSWER GENERATION
    # ============================================================

    def generate_answer(
        self,
        question,
        rows,
    ):

        start = time.time()

        if not rows:

            answer = "No records found."

        elif len(rows) == 1 and len(rows[0]) == 1:

            value = rows[0][0]

            if "how many" in question.lower():

                if isinstance(
                    value,
                    (int, float),
                ):

                    answer = f"There are " f"{value:,} records."

                else:

                    answer = str(value)

            else:

                answer = str(value)

        elif len(rows) <= 20:

            answer = self.result_generator.generate(
                question,
                rows,
            )

        else:

            answer = f"Found " f"{len(rows)} records."

        print(f"[TIMING] Answer generation = " f"{time.time() - start:.3f}s")

        return answer

    # ============================================================
    # SEMANTIC SAFETY GUARD
    # ============================================================

    @staticmethod
    def semantic_guard(
        question,
    ):

        q = question.lower()

        awb_math = re.search(
            r"\b(?:average|avg|sum|minimum|min|maximum|max)" r"\b.*\bawb\b",
            q,
        )

        if awb_math:

            return {
                "type": "error",
                "message": (
                    "AWB is an identifier, "
                    "not a numeric measure. "
                    "It cannot be averaged, "
                    "summed, minimized, "
                    "or maximized."
                ),
            }

        return None

    # ============================================================
    # QUESTION OPERATION
    # ============================================================

    @staticmethod
    def _question_operation(
        question: str,
    ) -> Optional[str]:

        q = question.lower()

        # --------------------------------------------------------
        # COUNT
        # --------------------------------------------------------
        #
        # Check these first because:
        # "total shipments" means a count,
        # not SUM(AWB).
        #

        if re.search(
            r"\bhow many\b",
            q,
        ):
            return "COUNT"

        if re.search(
            r"\bnumber of\b",
            q,
        ):
            return "COUNT"

        if re.search(
            r"\bcount(?: of)?\b",
            q,
        ):
            return "COUNT"

        if re.search(
            r"\btotal shipments?\b",
            q,
        ):
            return "COUNT"

        if re.search(
            r"\btotal awbs?\b",
            q,
        ):
            return "COUNT"

        if re.search(
            r"\bnumber of awbs?\b",
            q,
        ):
            return "COUNT"

        # --------------------------------------------------------
        # AVG
        # --------------------------------------------------------

        if re.search(
            r"\b(?:average|avg|mean)\b",
            q,
        ):
            return "AVG"

        # --------------------------------------------------------
        # SUM
        # --------------------------------------------------------

        if re.search(
            r"\b(?:sum|total)\b",
            q,
        ):
            return "SUM"

        # --------------------------------------------------------
        # MAX
        # --------------------------------------------------------

        if re.search(
            r"\b(?:maximum|max|highest)\b",
            q,
        ):
            return "MAX"

        # --------------------------------------------------------
        # MIN
        # --------------------------------------------------------

        if re.search(
            r"\b(?:minimum|min|lowest)\b",
            q,
        ):
            return "MIN"

        return None

    # ============================================================
    # SQL OPERATION
    # ============================================================

    @staticmethod
    def _sql_operation(
        sql: str,
    ) -> Optional[str]:

        try:

            tree = sqlglot.parse_one(
                sql,
                read="mysql",
            )

        except Exception:

            return None

        if tree.find(exp.Avg):
            return "AVG"

        if tree.find(exp.Sum):
            return "SUM"

        if tree.find(exp.Max):
            return "MAX"

        if tree.find(exp.Min):
            return "MIN"

        if tree.find(exp.Count):
            return "COUNT"

        return None

    # ============================================================
    # QUESTION COLUMN EXTRACTION
    # ============================================================

    @staticmethod
    def _question_columns(
        question: str,
    ) -> Set[str]:

        q = question.lower()

        columns = set()

        # --------------------------------------------------------
        # AWB
        # --------------------------------------------------------

        if re.search(
            r"\bawb\b",
            q,
        ):

            columns.add("awb")

        # --------------------------------------------------------
        # MOP
        # --------------------------------------------------------

        if re.search(
            r"\bmop\b",
            q,
        ):

            columns.add("mop")

        # --------------------------------------------------------
        # LIABILITY AMT
        # --------------------------------------------------------

        if "liability amount" in q or "liability amt" in q:

            columns.add("liability amt")

        # --------------------------------------------------------
        # LIABILITY
        # --------------------------------------------------------

        elif re.search(
            r"\bliability\b",
            q,
        ):

            columns.add("liability")

        # --------------------------------------------------------
        # AGE
        # --------------------------------------------------------

        if re.search(
            r"\bage\b",
            q,
        ):

            columns.add("age")

        # --------------------------------------------------------
        # PINCODE
        # --------------------------------------------------------

        if re.search(
            r"\bpincode\b",
            q,
        ):

            columns.add("pincode")

        # --------------------------------------------------------
        # SELLER
        # --------------------------------------------------------

        if "seller" in q:

            columns.add("seller name")

        # --------------------------------------------------------
        # CLIENT
        # --------------------------------------------------------

        if "client" in q:

            columns.add("client")

        # --------------------------------------------------------
        # ORDER ID
        # --------------------------------------------------------

        if "order id" in q or "order ids" in q:

            columns.add("order id")

        # --------------------------------------------------------
        # STATUS
        # --------------------------------------------------------

        if "status" in q or "statuses" in q:

            columns.add("status")

        # --------------------------------------------------------
        # MOVEMENT
        # --------------------------------------------------------

        if "movement" in q or "movement type" in q or "movement types" in q:

            columns.add("movement")

        # --------------------------------------------------------
        # TYPE
        # --------------------------------------------------------

        if "shipment type" in q or "shipment types" in q:

            columns.add("type")

        # --------------------------------------------------------
        # FINANCIAL YEAR
        # --------------------------------------------------------

        if "financial year" in q or "financial years" in q:

            columns.add("fy")

        # --------------------------------------------------------
        # YEAR
        # --------------------------------------------------------

        elif re.search(
            r"\byears?\b",
            q,
        ):

            columns.add("year")

        # --------------------------------------------------------
        # MONTH
        # --------------------------------------------------------

        if re.search(
            r"\bmonths?\b",
            q,
        ):

            columns.add("month")

        # --------------------------------------------------------
        # ROWS
        # --------------------------------------------------------

        if re.search(
            r"\brows?\b",
            q,
        ):

            columns.add("__rows__")

        return columns

    # ============================================================
    # SQL COLUMN EXTRACTION
    # ============================================================

    @staticmethod
    def _sql_columns(
        sql: str,
    ) -> Set[str]:

        try:

            tree = sqlglot.parse_one(
                sql,
                read="mysql",
            )

        except Exception:

            return set()

        columns = set()

        for column in tree.find_all(exp.Column):

            name = column.name.strip().lower()

            if name:
                columns.add(name)

        return columns

    # ============================================================
    # MEMORY SQL SAFETY CHECK
    # ============================================================

    def _memory_sql_matches_question(
        self,
        question: str,
        sql: str,
    ) -> bool:

        requested_operation = self._question_operation(question)

        actual_operation = self._sql_operation(sql)

        # --------------------------------------------------------
        # OPERATION CHECK
        # --------------------------------------------------------

        if requested_operation is not None:

            if actual_operation is None:

                print(
                    "[MEMORY] Rejected cached SQL: " "unable to detect SQL operation."
                )

                return False

            if requested_operation != actual_operation:

                print(
                    "[MEMORY] Rejected cached SQL: "
                    f"question_operation="
                    f"{requested_operation}, "
                    f"sql_operation="
                    f"{actual_operation}"
                )

                return False

        # --------------------------------------------------------
        # COLUMN / MEASURE CHECK
        # --------------------------------------------------------

        requested_columns = self._question_columns(question)

        actual_columns = self._sql_columns(sql)

        # "rows" is not a real column.
        requested_columns.discard("__rows__")

        # If the question clearly identifies
        # fields, those fields must appear in SQL.
        if requested_columns:

            normalized_actual = {
                value.replace(
                    "_",
                    " ",
                )
                for value in actual_columns
            }

            for requested in requested_columns:

                # Handle SQLGlot / alias normalization.
                requested_normalized = requested.replace(
                    "_",
                    " ",
                )

                if requested_normalized not in normalized_actual:

                    print(
                        "[MEMORY] Rejected cached SQL: "
                        f"requested column="
                        f"'{requested}', "
                        f"SQL columns="
                        f"{sorted(actual_columns)}"
                    )

                    return False

        return True

    # ============================================================
    # ASK
    # ============================================================

    def ask(
        self,
        question,
    ):

        total_start = time.time()

        original_question = question

        # ========================================================
        # SEMANTIC GUARD
        # ========================================================

        guard_result = self.semantic_guard(original_question)

        if guard_result:

            print("[SQL_ENGINE] " "Semantic guard rejected query.")

            return guard_result

        # ========================================================
        # NORMALIZATION
        # ========================================================

        start = time.time()

        question = normalize(question)

        print("\n========== NORMALIZER ==========")

        print(
            "Original   :",
            original_question,
        )

        print(
            "Normalized :",
            question,
        )

        print(f"[TIMING] Normalizer = " f"{time.time() - start:.3f}s")

        # ========================================================
        # MEMORY SEARCH
        # ========================================================

        start = time.time()

        memory_result = self.memory.search(
        question
)

        print(
            f"[TIMING] Memory search = "
            f"{time.time() - start:.3f}s"
        )


        memory_hit = False
        sql = None

# ========================================================
# EXPERIENCE VERIFICATION
# ========================================================

        if memory_result is not None:

            verification = self.experience_verifier.verify(
                matched_question=memory_result["matched_question"],
                sql=memory_result["sql"],
                similarity=memory_result["similarity"],
            )

            print(
                f"[MEMORY] Experience verification: "
                f"{verification}"
            )

            if verification["trusted"]:

                memory_hit = True
                sql = memory_result["sql"]

                print(
                    "[MEMORY] TRUSTED EXPERIENCE"
                )

                print(
                    "\n========== MEMORY SQL =========="
                )

                print(sql)

            else:

                print(
                    "[MEMORY] Experience not trusted: "
                    f"{verification['reason']}"
                )

        else:

            print(
                "[MEMORY] No similar experience found."
            )


# ========================================================
# SQL GENERATION
# ========================================================

        if not memory_hit:

            print(
                "🤖 GENERATING SQL"
            )

            log(
                "SQL_ENGINE",
                "Generating SQL",
            )

            try:

                sql = self.generate_sql(
                    question
                )

            except Exception as exc:

                return {
                    "type": "error",
                    "message": str(exc),
                }


# ========================================================
# VALIDATION
# ========================================================

        start = time.time()

        validation = (
            self.validator.validate(
                sql,
                question,
            )
        )

        print(
            "\n========== VALIDATOR =========="
        )

        print(validation)

        print(
            f"[TIMING] SQL validation = "
            f"{time.time() - start:.3f}s"
        )

        valid = (
            validation["decision"]
            == "PASS"
        )


# ========================================================
# INVALID SQL
# ========================================================

        if not valid:

            # ----------------------------------------------------
            # If trusted memory failed validation, regenerate.
            # ----------------------------------------------------

            if memory_hit:

                print(
                    "[MEMORY] Trusted SQL failed validation."
                )

                print(
                    "[MEMORY] Regenerating SQL."
                )

                memory_hit = False

            try:

                sql = self.generate_sql(
                    question
                )

            except Exception as exc:

                return {
                    "type": "error",
                    "message": str(exc),
                }

            validation = (
                self.validator.validate(
                    sql,
                    question,
                )
            )

            valid = (
                validation["decision"]
                == "PASS"
            )

        # ----------------------------------------------------
        # Generated SQL also failed.
        # ----------------------------------------------------

        if not valid:

            print(
                "[SQL_ENGINE] "
                "Generated SQL failed validation."
            )

            return {
                "type": "error",
                "message": (
                    validation["reason"]
                ),
            }

        # ========================================================
        # SELF EVALUATION
        # ========================================================

        if memory_hit:

            evaluation = {
                "score": 100,
                "decision": "PASS",
                "reason": (
                    "Trusted SQL memory "
                    "match passed operation, "
                    "column and schema checks."
                ),
            }

        elif self.enable_self_evaluation:

            start = time.time()

            evaluation = self.evaluator.evaluate(
                question,
                sql,
            )

            print("\n========== " "SELF EVALUATION " "==========")

            print(evaluation)

            print(f"[TIMING] Self evaluation = " f"{time.time() - start:.3f}s")

            # ----------------------------------------------------
            # SELF-EVALUATION RETRY
            # ----------------------------------------------------

            if (
                evaluation.get(
                    "score",
                    0,
                )
                < 85
            ):

                print("\n========== " "SELF EVALUATION RETRY " "==========")

                try:

                    sql = self.retry_sql(
                        question,
                        sql,
                        evaluation.get(
                            "reason",
                            "Low evaluation score",
                        ),
                    )

                    retry_validation = self.validator.validate(
                        sql,
                        question,
                    )

                    print("\n========== " "RETRY VALIDATOR " "==========")

                    print(retry_validation)

                    if retry_validation["decision"] == "PASS":

                        evaluation = self.evaluator.evaluate(
                            question,
                            sql,
                        )

                    else:

                        return {
                            "type": "error",
                            "message": (retry_validation["reason"]),
                        }

                except Exception as exc:

                    return {
                        "type": "error",
                        "message": str(exc),
                    }

        else:

            evaluation = {
                "score": 100,
                "decision": "PASS",
                "reason": ("SQLGlot/schema validation " "passed."),
            }

            print("[SQL_ENGINE] " "Self evaluation disabled " "for fast path.")

        # ========================================================
        # CONFIDENCE
        # ========================================================

        if memory_hit:

            confidence = {
                "score": 95,
                "level": "HIGH",
            }

        else:

            confidence = self.confidence.calculate(
                evaluation,
                valid,
            )

        print("\n========== CONFIDENCE ==========")

        print(confidence)

        # ========================================================
        # LOW CONFIDENCE RETRY
        # ========================================================

        if not memory_hit and confidence["score"] < 80:

            MAX_RETRY = 2

            for retry_number in range(
                1,
                MAX_RETRY + 1,
            ):

                print(
                    f"\n========== "
                    f"CONFIDENCE RETRY "
                    f"{retry_number} "
                    f"=========="
                )

                try:

                    sql = self.retry_sql(
                        question,
                        sql,
                        "Low confidence score",
                    )

                    validation = self.validator.validate(
                        sql,
                        question,
                    )

                    print("\n========== " "RETRY VALIDATOR " "==========")

                    print(validation)

                    if validation["decision"] != "PASS":

                        continue

                    evaluation = self.evaluator.evaluate(
                        question,
                        sql,
                    )

                    confidence = self.confidence.calculate(
                        evaluation,
                        True,
                    )

                    print(confidence)

                    if confidence["score"] >= 80:

                        break

                except Exception as exc:

                    print(
                        "[SQL_ENGINE] " "Confidence retry failed:",
                        exc,
                    )

        if confidence["score"] < 80:

            return {
                "type": "error",
                "message": (
                    "Unable to generate reliable SQL " "after multiple retries."
                ),
            }

        # ========================================================
        # FINAL VALIDATION
        # ========================================================

        validation = self.validator.validate(
            sql,
            question,
        )

        if validation["decision"] != "PASS":

            return {
                "type": "error",
                "message": (validation["reason"]),
            }

        # ========================================================
        # EXECUTION + SELF HEAL
        # ========================================================

        MAX_EXECUTION_RETRIES = 2

        execution_retry = 0

        original_failed_sql = None

        last_error = None

        result = None

        while execution_retry <= MAX_EXECUTION_RETRIES:

            try:

                log(
                    "SQL_ENGINE",
                    "Executing SQL",
                )

                result = self.execute_sql(sql)

                # ------------------------------------------------
                # Successful self-heal
                # ------------------------------------------------

                if original_failed_sql is not None:

                    self.learner.save_correction(
                        question=question,
                        failed_sql=(original_failed_sql),
                        corrected_sql=sql,
                        error_message=(last_error),
                        success=True,
                    )

                    print("\n========== " "SQL SELF-HEAL SUCCESS " "==========")

                break

            except Exception as exc:

                error_message = str(exc)

                print("\n========== " "SQL EXECUTION ERROR " "==========")

                print(error_message)

                # ------------------------------------------------
                # Save original failure once
                # ------------------------------------------------

                if original_failed_sql is None:

                    original_failed_sql = sql

                    last_error = error_message

                    self.learner.save_correction(
                        question=question,
                        failed_sql=sql,
                        corrected_sql=None,
                        error_message=(error_message),
                        success=False,
                    )

                execution_retry += 1

                if execution_retry > MAX_EXECUTION_RETRIES:

                    return {
                        "type": "error",
                        "message": (error_message),
                    }

                print(
                    f"\n========== "
                    f"SQL SELF-HEAL RETRY "
                    f"{execution_retry} "
                    f"=========="
                )

                try:

                    sql = self.retry_sql(
                        question,
                        sql,
                        error_message,
                    )

                except Exception as retry_exc:

                    print("\n========== " "RETRY SQL ERROR " "==========")

                    print(retry_exc)

                    continue

                retry_validation = self.validator.validate(
                    sql,
                    question,
                )

                print("\n========== " "RETRY VALIDATOR " "==========")

                print(retry_validation)

                if retry_validation["decision"] != "PASS":

                    continue

        if result is None:

            return {
                "type": "error",
                "message": ("SQL execution failed " "after retries."),
            }

        # ========================================================
        # MEMORY SAVE
        # ========================================================

        if not memory_hit:

            start = time.time()

            self.memory.save_sql(
                question=question,
                sql=sql,
                execution_time=result["time"],
            )

            print(f"[TIMING] Memory save = " f"{time.time() - start:.3f}s")

        else:

            print("[MEMORY] Existing SQL reused - " "skipping memory save")

        # ========================================================
        # ANSWER
        # ========================================================

        answer = self.generate_answer(
            question,
            result["rows"],
        )

        result["answer"] = answer

        # ========================================================
        # LEARNING
        # ========================================================

        start = time.time()

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

        print(f"[TIMING] Learner save = " f"{time.time() - start:.3f}s")

        result["log_id"] = log_id

        print("\n========================================")

        print(f"[TIMING] TOTAL ASK = " f"{time.time() - total_start:.3f}s")

        print("========================================")

        return result

    # ============================================================
    # RETRY SQL
    # ============================================================

    def retry_sql(
        self,
        question,
        previous_sql,
        reason,
    ):

        prompt = f"""
You are a MySQL SQL correction engine.

User Question:
{question}

Previous SQL:
{previous_sql}

Problem:
{reason}

Rules:
1. Return ONLY one valid MySQL SELECT statement.
2. No explanation.
3. No markdown.
4. No comments.
5. Use ONLY columns that exist in the supplied database schema.
6. NEVER invent a column.
7. AWB is an identifier.
8. Do not use AVG, SUM, MIN or MAX on AWB.
9. Preserve the requested aggregation from the user.
10. Preserve the requested measure/column from the user.

Return ONLY SQL.
"""

        response = self.router.sql().invoke(prompt)

        raw_sql = response.content.strip()

        print("\n========== " "RAW RETRY RESPONSE " "==========")

        print(raw_sql)

        sql = self.sql_builder.build(raw_sql)

        sql = self.sql_optimizer.optimize(sql)

        print("\n========== RETRY SQL ==========")

        print(sql)

        return sql
