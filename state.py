class SessionState:
    def __init__(self, session_id: str, user_id: str):
        self.name=None
        self.reason=None
        self.date=None
        self.step="greeting"
        self.turn_count = 0


        