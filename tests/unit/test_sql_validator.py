from src.sql_validator import SQLValidator


def validator():
    return SQLValidator("""Table: ajio
- AWB
- Value
Table: purple
- AWB
""")


def test_mysql_select_and_cte_are_valid():
    result = validator().validate("WITH shipments AS (SELECT AWB FROM ajio) SELECT COUNT(*) FROM shipments")
    assert result["decision"] == "PASS"


def test_destructive_sql_and_unknown_tables_are_rejected():
    assert validator().validate("DELETE FROM ajio")["decision"] == "FAIL"
    assert validator().validate("SELECT * FROM unknown_table")["decision"] == "FAIL"


def test_awb_is_not_summed_without_explicit_request():
    assert validator().validate("SELECT SUM(AWB) FROM ajio", "total shipments")["decision"] == "FAIL"
    assert validator().validate("SELECT COUNT(DISTINCT AWB) FROM ajio", "total shipments")["decision"] == "PASS"
