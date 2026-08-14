import json
import os


class MetadataStore:

    def __init__(self):

        os.makedirs("data/metadata", exist_ok=True)

        self.file = "data/metadata/business_glossary.json"

        if not os.path.exists(self.file):
            with open(self.file, "w") as f:
                json.dump([], f, indent=4)

    def load(self):

        with open(self.file, "r") as f:
            return json.load(f)

    def save(self, data):

        with open(self.file, "w") as f:
            json.dump(data, f, indent=4)

    def find(self, column):

        column = column.lower()

        data = self.load()

        for item in data:

            if item["column"].lower() == column:
                return item

            aliases = [a.lower() for a in item.get("aliases", [])]

            if column in aliases:
                return item

        return None

    def add(self, metadata):

        data = self.load()

        data.append(metadata)

        self.save(data)