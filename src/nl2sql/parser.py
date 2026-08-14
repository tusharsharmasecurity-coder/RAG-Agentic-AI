import re

from src.text_normalizer import normalize


class QuestionParser:
    """
    Converts Natural Language into a structured representation
    before SQL generation.
    """

    def __init__(self):

        self.metric_mapping = {
            "shipment": "AWB",
            "shipments": "AWB",
            "awb": "AWB",
            "tracking": "AWB",
            "tracking number": "AWB",
            "tracking id": "AWB",
            "weight": "Weight",
            "value": "Value",
            "amount": "Value",
            "price": "Value",
            "cost": "Value",
            "warehouse": "DC",
            "hub": "DC",
            "center": "DC",
            "dc": "DC",
            "status": "Validation",
            "closure": "Closure",
            "date": "LSD",
            "shipment date": "LSD",
            "delivery date": "LSD",
        }

    # ---------------------------------------------------------

    def parse(self, question: str):

        normalized_question = normalize(question)
        q = normalized_question.lower()

        result = {
            "normalized": normalized_question,
            "intent": "select",
            "metrics": [],
            "filters": [],
            "group_by": None,
            "time": None,
            "sort": None,
            "limit": None,
        }

        # -------------------------------------------------
        # Intent Detection
        # -------------------------------------------------

        count_words = [
            "how many",
            "count",
            "number of",
            "total shipments",
            "shipment count",
            "total awb",
            "overall shipments",
        ]

        if any(word in q for word in count_words):
            result["intent"] = "count"

        elif any(x in q for x in ["average", "avg"]):
            result["intent"] = "average"

        elif any(x in q for x in ["sum", "total revenue", "total value"]):
            result["intent"] = "sum"

        elif any(x in q for x in ["maximum", "highest", "max"]):
            result["intent"] = "max"

        elif any(x in q for x in ["minimum", "lowest", "min"]):
            result["intent"] = "min"

        # -------------------------------------------------
        # Metric Detection
        # -------------------------------------------------

        for word, column in self.metric_mapping.items():

            if word in q:

                if column not in result["metrics"]:
                    result["metrics"].append(column)

        # -------------------------------------------------
        # GROUP BY
        # -------------------------------------------------

        group_words = [
            "by warehouse",
            "by dc",
            "per warehouse",
            "per dc",
            "warehouse wise",
            "dc wise",
            "group by warehouse",
            "group by dc",
        ]

        if any(word in q for word in group_words):
            result["group_by"] = "DC"

        # -------------------------------------------------
        # TOP / LIMIT
        # -------------------------------------------------

        if "top" in q:

            result["sort"] = "DESC"

            number = re.search(r"top\s+(\d+)", q)

            if number:
                result["limit"] = int(number.group(1))
            else:
                result["limit"] = 10

        if "bottom" in q:

            result["sort"] = "ASC"

            number = re.search(r"bottom\s+(\d+)", q)

            if number:
                result["limit"] = int(number.group(1))
            else:
                result["limit"] = 10

        # -------------------------------------------------
        # DATE FILTERS
        # -------------------------------------------------

        if "today" in q:
            result["time"] = "today"

        elif "yesterday" in q:
            result["time"] = "yesterday"

        elif "last week" in q:
            result["time"] = "last_week"

        elif "this week" in q:
            result["time"] = "this_week"

        elif "last month" in q:
            result["time"] = "last_month"

        elif "this month" in q:
            result["time"] = "this_month"

        elif "this year" in q:
            result["time"] = "this_year"

        elif "last year" in q:
            result["time"] = "last_year"

        # -------------------------------------------------
        # FILTERS
        # -------------------------------------------------

        warehouses = [
            "blr",
            "bangalore",
            "kolkata",
            "delhi",
            "mumbai",
            "hyderabad",
            "chennai",
            "pune",
        ]

        for city in warehouses:

            if city in q:

                result["filters"].append({"column": "DC", "value": city})

        status_words = [
            "open",
            "closed",
            "pending",
            "delivered",
            "lost",
        ]

        for status in status_words:

            if status in q:

                result["filters"].append({"column": "Validation", "value": status})

        # -------------------------------------------------
        # DISTINCT
        # -------------------------------------------------

        if "distinct" in q or "unique" in q:
            result["distinct"] = True
        else:
            result["distinct"] = False

        return result

    # ---------------------------------------------------------

    def process(self, question):

        parsed = self.parse(question)

        print("\n========== NL2SQL PARSER ==========")

        for k, v in parsed.items():
            print(f"{k}: {v}")

        return parsed
