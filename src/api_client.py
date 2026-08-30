import requests


API_URL = "http://127.0.0.1:8000"


def ask_agent(question: str):
    response = requests.post(
        f"{API_URL}/ask",
        json={
            "question": question
        },
        timeout=120,
    )

    response.raise_for_status()

    data = response.json()

    return data