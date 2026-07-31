class ChatMemory:

    def __init__(self):
        self.history = []

    def add_user(self, text):
        self.history.append(("User", text))

    def add_ai(self, text):
        self.history.append(("AI", text))

    def get_context(self, limit=6):
        history = self.history[-limit:]
        return "\n".join(f"{role}: {msg}" for role, msg in history)

    def clear(self):
        self.history = []