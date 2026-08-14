"""
Reusable SQL templates for the SQL Builder.
"""

# ---------------------------------------------------
# Base UNION of all shipment tables
# ---------------------------------------------------

UNION_ALL_TABLES = """
(
    SELECT * FROM ajio
    UNION ALL
    SELECT * FROM ajio2
    UNION ALL
    SELECT * FROM purple
) AS combined
"""

# ---------------------------------------------------
# Aggregation templates
# ---------------------------------------------------

COUNT_TEMPLATE = "COUNT(DISTINCT {column}) AS {alias}"

SUM_TEMPLATE = "SUM({column}) AS {alias}"

AVG_TEMPLATE = "AVG({column}) AS {alias}"

MAX_TEMPLATE = "MAX({column}) AS {alias}"

MIN_TEMPLATE = "MIN({column}) AS {alias}"

# ---------------------------------------------------
# Simple SELECT
# ---------------------------------------------------

SELECT_TEMPLATE = "SELECT {columns}"

SELECT_DISTINCT_TEMPLATE = "SELECT DISTINCT {columns}"