import time
import sys

def log(message: str, delay: float = 0.02):
    """Affichage caractère par caractère (effet terminal)"""
    for char in message:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def phase(title: str):
    print()
    log(f"[INITIALISATION] :: {title}", 0.03)
    time.sleep(0.5)


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def success(message: str):
    log(f"[OK] :: {message}", 0.02)
    time.sleep(0.3)


""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def loading(message: str, duration: float = 1.5):
    log(f"[LOADING] :: {message}", 0.02)
    steps = int(duration / 0.3)
    for i in range(steps):
        log(f"   > progression {int((i+1)/steps*100)}%", 0.01)
        time.sleep(0.3)
