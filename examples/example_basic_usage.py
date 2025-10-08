import os
import sys
import time

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC_DIR = os.path.join(BASE_DIR, 'src')
for p in (SRC_DIR, BASE_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from consolio import Consolio  
except ModuleNotFoundError:
    import consolio  
    Consolio = consolio.Consolio


def main():
    console = Consolio(spinner_type="dots")

    console.print("inf", "Welcome to Consolio demo!")
    console.print(1, "wip", "Preparing environment...")

    with console.spinner("Working hard...", inline=True):
        time.sleep(2)

    console.print(1, "cmp", "Spinner demo complete.")

    with console.progress(indent=1, initial_percentage=0) as update:
        for i in range(0, 101, 20):
            time.sleep(0.25)
            update(i)

    console.print(1, "cmp", "Progress demo complete.")

    user = console.input(0, "Enter your name:", inline=True)
    console.print(0, "cmp", f"Hello, {user}! All systems operational.")


if __name__ == "__main__":
    main()
