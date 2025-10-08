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
    console = Consolio(spinner_type="default")

    console.plain()

    console.print("inf", "Plain mode demo")
    console.print(1, "wip", "No colors, no spinner animations here")

    with console.spinner("This will not animate", inline=True):
        time.sleep(0.5)

    with console.progress(indent=1, initial_percentage=0) as update:
        for i in range(0, 101, 50):
            time.sleep(0.2)
            update(i)

    console.print(1, "cmp", "Done in plain mode.")


if __name__ == "__main__":
    main()
