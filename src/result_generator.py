class ResultGenerator:

    def generate(self, question, rows):

        if not rows:
            return "No matching records were found."

        # ----------------------------
        # Single value
        # ----------------------------

        if len(rows) == 1 and len(rows[0]) == 1:

            value = rows[0][0]

            q = question.lower()

            if "count" in q or "how many" in q or "shipment" in q or "awb" in q:

                return f"Total AWB: {value}"

            return str(value)

        # ----------------------------
        # Small table
        # ----------------------------

        if len(rows) <= 10:

            return f"Found {len(rows)} records."

        return f"Found {len(rows)} records."