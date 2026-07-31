import re
from src.sql_validator import SQLValidator
from src.database import Database
from src.prompt import SQL_SYSTEM_PROMPT
from src.llm import invoke

import time
from src.result_generator import ResultGenerator
from src.memory.memory_manager import MemoryManager
from src.schema.schema_retriever import SchemaRetriever
from src.sql.self_healer import SQLSelfHealer
class SQLEngine:

    def __init__(self):
        self.db = Database()
        self.connection = self.db.connection
        self.memory = MemoryManager()
        self.schema_retriever = SchemaRetriever()
        self.self_healer = SQLSelfHealer()
        # Load schema once
        self.schema = self.get_schema()
        self.result_generator = ResultGenerator()
        print("[INFO] SQL Engine Ready")

    # ---------------------------------
    # Get database schema
    # ---------------------------------
    def get_schema(self):

        cursor = self.db.connection.cursor()

        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        schema = ""

        for (table,) in tables:
            print("Reading table:", repr(table))

            schema += f"\nTable: {table}\n"

            cursor.execute(f"SHOW COLUMNS FROM `{table}`")

            columns = cursor.fetchall()

            for column in columns:
                schema += f"- {column[0]}\n"

        cursor.close()

        return schema

    # ---------------------------------
    # Validate SQL
    # ---------------------------------
    def validate_sql(self, sql: str):

        sql = sql.strip().lower()

        if not sql.startswith("select"):
            raise ValueError("Only SELECT queries are allowed.")

        blocked = [
            "delete",
            "update",
            "insert",
            "drop",
            "alter",
            "truncate",
            "create",
            "grant",
            "revoke"
        ]

        for word in blocked:
            if word in sql:
                raise ValueError(f"Blocked SQL detected: {word}")

        return True

    # ---------------------------------
    # Generate SQL
    # ---------------------------------
    def generate_sql(self, question: str):
     print(">>> NEW generate_sql() is running")
     # Build prompt
     relevant = self.schema_retriever.retrieve(question)

     schema_text = ""

     if relevant:

      for table in relevant:

        schema_text += f"\nTable: {table['table']}\n"

        for col in table["columns"]:

            schema_text += f"- {col}\n"

     else:

      schema_text = self.schema

      prompt = SQL_SYSTEM_PROMPT.format(
       schema=schema_text,
       question=question
       )
      print("\n===== Relevant Schema =====")
      print(schema_text)
      print("===========================\n")

    # Call the LLM
     response = invoke(prompt)

    # Get SQL text
     sql = response.content.strip()

    # Remove markdown if the model returns ```sql
     sql = re.sub(r"```sql|```", "", sql).strip()

    # Handle impossible queries
     if sql == "CANNOT_GENERATE_SQL":
        return sql

     return sql

    # ---------------------------------
    # Execute SQL
    # ---------------------------------
    def execute_sql(self, sql):

        self.validate_sql(sql)

        cursor = self.db.connection.cursor()

        try:

            start = time.time()
            cursor.execute(sql)

            rows = cursor.fetchall()
            elapsed = round(time.time() - start, 4)

            columns = [col[0] for col in cursor.description]
            row_count = len(rows)
            return {
                     "type":"table",
                     "sql":sql,
                     "time":elapsed,
                     "columns":columns,
                      "rows":rows
                     }

        except Exception as e:

            return {
                "type": "error",
                "message": str(e)
            }

        finally:

            cursor.close()

    # ---------------------------------
    # Main function
    # ---------------------------------
    def ask(self, question):

    # ============================
    # 1. Check Memory
    # ============================

     saved_sql = self.memory.search(question)
     print(type(saved_sql))
     print(saved_sql)

     if saved_sql:

        print("🧠 SQL loaded from memory")

        result = self.execute_sql(saved_sql)

        if result["type"] == "table":

            self.memory.increase_usage(question)

            rows = result["rows"]

            if len(rows) <= 20:

                result["answer"] = self.result_generator.generate(
                    question,
                    rows
                )

            else:

                result["answer"] = f"Found {len(rows)} records."
                result["rows"] = rows[:100]

        return result


    # ============================
    # 2. Generate SQL
    # ============================

     sql = self.generate_sql(question)

     if sql == "CANNOT_GENERATE_SQL":

        return {
            "type": "error",
            "message": "The requested information does not exist in the database."
        }


    # ============================
    # 3. Validate SQL
    # ============================

     validator = SQLValidator(self.schema)
     sql = self.generate_sql(question)
     valid, message = validator.validate(sql)

     if not valid:

        return {
            "type": "error",
            "message": message
        }

     print("\nGenerated SQL:")
     print(sql)


    # ============================
    # 4. Execute SQL
    # ============================

     result = self.execute_sql(sql)

     if result["type"] == "error":

        return result


    # ============================
    # 5. Save to Memory
    # ============================

     self.memory.save_sql(

        question=question,

        sql=sql,

        execution_time=result["time"]

     )


    # ============================
    # 6. Generate Answer
    # ============================

     rows = result["rows"]

     if len(rows) <= 20:

        result["answer"] = self.result_generator.generate(
            question,
            rows
        )

     else:

        result["answer"] = f"Found {len(rows)} records."
        result["rows"] = rows[:100]

     return result