from datetime import datetime


def log(component, message):

    print(
        f"[{datetime.now().strftime('%H:%M:%S')}] [{component}] {message}"
    )