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
    "in"
}


def normalize(question):

    question = question.lower()

    # Remove punctuation
    question = re.sub(r"[^a-z0-9 ]", " ", question)

    # Replace ONLY whole words / phrases
    for key, value in sorted(
        BUSINESS_TERMS.items(),
        key=lambda x: len(x[0]),
        reverse=True,
    ):

        pattern = r"\b" + re.escape(key) + r"\b"

        question = re.sub(
            pattern,
            value,
            question
        )

    words = []

    for word in question.split():

        if word not in STOP_WORDS:

            words.append(word)

    return " ".join(words)