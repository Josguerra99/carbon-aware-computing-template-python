allow_debug_logs = False


def log(message: str) -> None:
    if allow_debug_logs:
        print(message)
