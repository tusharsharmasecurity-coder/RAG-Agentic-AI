from src.nl2sql.parser import QuestionParser


class NL2SQLEngine:

    def __init__(self):
        self.parser = QuestionParser()

    def process(self, question):

        parsed = self.parser.parse(question)

        return {
            "original": question,
            "normalized": parsed["normalized"],
            "intent": parsed["intent"],
            "metrics": parsed["metrics"],
            "filters": parsed["filters"],
            "group_by": parsed["group_by"],
            "time": parsed["time"],
            "sort": parsed["sort"],
            "limit": parsed["limit"],
            "distinct": parsed["distinct"],
        }


print("NL2SQL loaded")
print(dir(NL2SQLEngine))