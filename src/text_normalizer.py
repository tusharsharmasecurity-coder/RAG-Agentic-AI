import re

from src.memory.business_dictionary import BUSINESS_TERMS

STOP_WORDS = {
    "how",
    "many",
    "show",
    "please",
    "can",
    "could",
    "you",
    "tell",
    "me",
    "the",
    "is",
    "are",
    "what",
    "all",
    "of",
    "in",
}

ABBREVIATIONS = {
    "hw": "how",
    "mny": "many",
    "shipmnt": "shipment",
    "shipmnts": "shipments",
    "shpmnt": "shipment",
    "shpmnts": "shipments",
}


def normalize(question):

    question = question.lower()

    question = re.sub(r"[^a-z0-9 ]", " ", question)

    words = [
        ABBREVIATIONS.get(word, word)
        for word in question.split()
    ]
    question = " ".join(words)

    # Preserve the count intent before removing conversational stop words.
    question = re.sub(r"\bhow\s+many\b", "count", question)

    for key, value in sorted(
        BUSINESS_TERMS.items(),
        key=lambda x: len(x[0]),
        reverse=True,
    ):

        pattern = r"\b" + re.escape(key) + r"\b"

        question = re.sub(pattern, value, question)

    normalized_words = []

    for word in question.split():

        if word not in STOP_WORDS:

            normalized_words.append(word)

    return " ".join(normalized_words)
