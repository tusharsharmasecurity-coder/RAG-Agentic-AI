from src.sql.self_healer import SQLSelfHealer

healer = SQLSelfHealer()

sql = """
SELECT COUNT(*)
FROM Call_record
"""

fixed = healer.heal(

    question="How many cx cut the call in ajio",

    sql=sql,

    error="Unknown table Call_record",

    schema="""
Table: ajio

AWB
Call record
Validation
Closure
"""
)

print(fixed)