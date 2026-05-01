import time
import sys

def log(message: str, delay: float = 0.02):
    for char in message:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def phase(title: str):
    print()
    log(f"[INIT] :: {title}", 0.03)
    time.sleep(0.5)

def success(message: str):
    log(f"[OK] :: {message}", 0.02)
    time.sleep(0.3)

def loading(message: str, duration: float = 1.5, width: int = 30):
    log(f"[LOADING] :: {message}", 0.02)
    steps = width
    for i in range(steps + 1):
        filled = "█" * i
        empty = "░" * (steps - i)
        percent = int((i / steps) * 100)
        sys.stdout.write(f"\r   [{filled}{empty}] {percent}%")
        sys.stdout.flush()
        time.sleep(duration / steps)
    print()