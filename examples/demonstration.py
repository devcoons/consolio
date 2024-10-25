import time
from consolio import Consolio

def main():
    spinner_types = ['default', 'braille', 'dots', 'star']

    for spinner in spinner_types:
        print(f"\nDemonstrating spinner: '{spinner}'")
        print("-" * 40)

        console = Consolio(spinner_type=spinner)

        console.sprint(0, 'str', 'Starting the process.')
        console.sprint(1, 'stp', 'Performing step 1.')
        console.start_animate(1)
        time.sleep(3)
        console.sprint(1, 'stp', 'Performing step 2.')
        console.start_animate(1)
        time.sleep(2)
        console.sprint(1, 'wrn', 'A warning occurred.')
        console.sprint(1, 'err', 'An error occurred.')
        console.sprint(0, 'cmp', 'Process completed.')

        time.sleep(2)

if __name__ == "__main__":
    main()
