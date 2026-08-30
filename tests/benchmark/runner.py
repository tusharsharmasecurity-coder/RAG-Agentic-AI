import json
import math
import time
from decimal import Decimal
from datetime import date, datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from src.database import Database

BASE_URL = "http://127.0.0.1:8000"
ROOT = Path(__file__).parent
QUESTIONS_FILE = ROOT / "questions.json"
RESULTS_DIR = ROOT / "results"

RESULTS_DIR.mkdir(exist_ok=True)


def ask_api(question):
    body = json.dumps({"question": question}).encode("utf-8")

    request = Request(
        f"{BASE_URL}/ask",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    start = time.perf_counter()

    try:
        with urlopen(request, timeout=180) as response:
            payload = json.loads(response.read().decode("utf-8"))

            return (
                response.status,
                payload,
                time.perf_counter() - start,
                None,
            )

    except HTTPError as exc:

        try:
            payload = json.loads(exc.read().decode("utf-8"))
        except Exception:
            payload = None

        return (
            exc.code,
            payload,
            time.perf_counter() - start,
            str(exc),
        )

    except Exception as exc:

        return (
            None,
            None,
            time.perf_counter() - start,
            str(exc),
        )


def normalize_value(value):

    if isinstance(
        value,
        (datetime, date),
    ):
        return value.isoformat()

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, float):

        if math.isclose(
            value,
            round(value),
            abs_tol=1e-9,
        ):
            return int(round(value))

        return round(value, 8)

    return value


def normalize_rows(rows):

    return [[normalize_value(value) for value in row] for row in rows]


def values_equal(a, b):

    if a is None or b is None:
        return a == b

    try:
        return math.isclose(
            float(a),
            float(b),
            rel_tol=1e-7,
            abs_tol=1e-6,
        )

    except Exception:

        return str(a).strip().lower() == str(b).strip().lower()


def rows_equal(expected, actual):

    if len(expected) != len(actual):
        return False

    for expected_row, actual_row in zip(
        expected,
        actual,
    ):

        if len(expected_row) != len(actual_row):
            return False

        for expected_value, actual_value in zip(
            expected_row,
            actual_row,
        ):

            if not values_equal(
                expected_value,
                actual_value,
            ):
                return False

    return True


def run_gold_sql(sql):

    db = Database()

    try:

        cursor = db.connection.cursor()

        cursor.execute(sql)

        rows = cursor.fetchall()

        columns = [column[0] for column in cursor.description]

        cursor.close()

        return (
            columns,
            normalize_rows(rows),
        )

    finally:

        db.close()


def score_case(case, payload):

    result = (payload or {}).get("result", {})

    intent = result.get("intent")

    answer = str(result.get("answer", "") or "")

    tool_result = result.get("tool_result")

    # ------------------------------------------------------------
    # SQL
    # ------------------------------------------------------------

    if case["category"] == "SQL":

        if intent != "SQL":
            return False, (f"Expected SQL, got {intent}")

        if not isinstance(
            tool_result,
            dict,
        ):
            return False, "Missing SQL result"

        actual_rows = normalize_rows(
            tool_result.get(
                "rows",
                [],
            )
        )

        _, expected_rows = run_gold_sql(case["gold_sql"])

        if rows_equal(
            expected_rows,
            actual_rows,
        ):
            return True, "SQL result matched"

        return False, (f"Expected {expected_rows}; " f"got {actual_rows}")

    # ------------------------------------------------------------
    # GUARD
    # ------------------------------------------------------------

    if case["category"] == "GUARD":

        phrase = case["expected_phrase"].lower()

        ok = intent == "SQL" and phrase in answer.lower()

        return (
            ok,
            "AWB safety guard triggered" if ok else answer,
        )

    # ------------------------------------------------------------
    # RAG
    # ------------------------------------------------------------

    if case["category"] == "RAG":

        if intent != "RAG":
            return False, (f"Expected RAG, got {intent}")

        missing = [
            keyword
            for keyword in case["expected_keywords"]
            if keyword.lower() not in answer.lower()
        ]

        if not missing:
            return True, ("Expected SOP facts found")

        return False, (f"Missing keywords: {missing}")

    # ------------------------------------------------------------
    # BOTH
    # ------------------------------------------------------------

    if case["category"] == "BOTH":

        if intent != "BOTH":
            return False, (f"Expected BOTH, got {intent}")

        if not isinstance(
            tool_result,
            dict,
        ):
            return False, ("Missing BOTH result")

        sql_result = tool_result.get(
            "sql_result",
            {},
        )

        actual_rows = normalize_rows(
            sql_result.get(
                "rows",
                [],
            )
        )

        _, expected_rows = run_gold_sql(case["gold_sql"])

        rag_text = str(
            tool_result.get(
                "rag_result",
                "",
            )
        )

        missing = [
            keyword
            for keyword in case["expected_keywords"]
            if keyword.lower() not in rag_text.lower()
        ]

        sql_ok = rows_equal(
            expected_rows,
            actual_rows,
        )

        rag_ok = not missing

        return (
            sql_ok and rag_ok,
            (
                "SQL + RAG matched"
                if sql_ok and rag_ok
                else (f"SQL ok={sql_ok}; " f"missing RAG={missing}")
            ),
        )

    # ------------------------------------------------------------
    # CHAT
    # ------------------------------------------------------------

    if case["category"] == "CHAT":

        ok = intent == "CHAT" and bool(answer.strip())

        return (
            ok,
            "Chat response returned" if ok else "Chat failed",
        )

    return False, ("Unknown benchmark category")


def main():

    cases = json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))

    results = []

    print(f"\nRunning {len(cases)} benchmark cases...")

    for index, case in enumerate(
        cases,
        start=1,
    ):

        print(f"\n[{index:02d}/{len(cases)}] " f"{case['id']} | " f"{case['question']}")

        status, payload, latency, error = ask_api(case["question"])

        try:

            passed, detail = score_case(
                case,
                payload,
            )

        except Exception as exc:

            passed = False
            detail = f"Benchmark error: {exc}"

        result = {
            "id": case["id"],
            "category": case["category"],
            "question": case["question"],
            "http_status": status,
            "latency_sec": round(
                latency,
                4,
            ),
            "passed": passed,
            "detail": detail,
            "intent": ((payload or {}).get("result", {}).get("intent")),
            "answer": ((payload or {}).get("result", {}).get("answer")),
            "error": error,
        }

        results.append(result)

        print(f"    {'PASS' if passed else 'FAIL'} " f"| {latency:.2f}s " f"| {detail}")

    total = len(results)

    passed = sum(1 for result in results if result["passed"])

    accuracy = passed / total * 100 if total else 0

    average_latency = (
        sum(result["latency_sec"] for result in results) / total if total else 0
    )

    categories = {}

    for result in results:

        category = result["category"]

        bucket = categories.setdefault(
            category,
            {
                "total": 0,
                "passed": 0,
                "latencies": [],
            },
        )

        bucket["total"] += 1

        bucket["passed"] += int(result["passed"])

        bucket["latencies"].append(result["latency_sec"])

    summary = {
        "total_cases": total,
        "passed": passed,
        "failed": total - passed,
        "accuracy_percent": round(
            accuracy,
            2,
        ),
        "average_latency_sec": round(
            average_latency,
            4,
        ),
        "by_category": {},
    }

    for category, bucket in categories.items():

        summary["by_category"][category] = {
            "total": bucket["total"],
            "passed": bucket["passed"],
            "accuracy_percent": round(
                bucket["passed"] / bucket["total"] * 100,
                2,
            ),
            "average_latency_sec": round(
                sum(bucket["latencies"]) / len(bucket["latencies"]),
                4,
            ),
        }

    timestamp = time.strftime("%Y%m%d_%H%M%S")

    output = {
        "summary": summary,
        "results": results,
    }

    output_file = RESULTS_DIR / f"benchmark_{timestamp}.json"

    output_file.write_text(
        json.dumps(
            output,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print("\n========== BENCHMARK SUMMARY ==========")

    print(
        json.dumps(
            summary,
            indent=2,
        )
    )

    print(f"\nSaved: {output_file}")


if __name__ == "__main__":
    main()
