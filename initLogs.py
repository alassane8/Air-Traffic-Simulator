import sys

def log(message: str, delay: float = 0.02):
    print(message)

def phase(title: str):
    print()
    print(f"[INIT] :: {title}")

def success(message: str):
    print(f"[OK] :: {message}")

def loading(message: str, duration: float = 1, width: int = 30):
    print(f"[LOADING] :: {message}")