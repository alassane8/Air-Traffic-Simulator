import sys
import time


def log(message: str):
    for char in message:
        sys.stdout.write(char)
        sys.stdout.flush()
    print()


def phase(title: str):
    print()
    log(f"[INIT] :: {title}")


def success(message: str):
    log(f"[OK] :: {message}")


def loading(message: str, duration: float = 1, width: int = 30):
    log(f"[LOADING] :: {message}")
    steps = width
    for i in range(steps + 1):
        filled = "█" * i
        empty = "░" * (steps - i)
        percent = int((i / steps) * 100)
        sys.stdout.write(f"\r   [{filled}{empty}] {percent}%")
        sys.stdout.flush()
        time.sleep(duration / steps)
    print()