class Logger:
    allow_debug_logs = False

    @classmethod
    def log(cls, message: str) -> None:
        if cls.allow_debug_logs:
            print(message)
