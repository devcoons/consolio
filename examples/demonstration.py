import time
from consolio import Consolio

def main():
    spinner_types = ['default', 'braille', 'dots']

    for spinner in spinner_types:
        print(f"\nDemonstrating spinners: '{spinner}'")
        print("-" * 40)

        console = Consolio(spinner_type=spinner)
        console.sprint(0, 'str', 'Starting demo process. (spinner under)')
        console.sprint(1, 'stp', 'Performing step 1.')
        console.start_animate(1)
        time.sleep(1.2)
        console.sprint(1, 'wrn', 'A warning occurred.')
        console.sprint(1, 'stp', 'Performing step 2.')
        console.start_animate(1)
        time.sleep(1.1)        
        console.sprint(1, 'err', 'Step 2 failed. An error occurred.')
        console.sprint(1, 'stp', 'Performing step 3.')
        console.start_animate(1)
        time.sleep(1.3)        
        console.sprint(1, 'cmp', 'Step 3 completed.')
        time.sleep(2)
        print("-" * 40)
        console.sprint(0, 'str', 'Starting demo process. (spinner inline/no-replace)')
        console.sprint(1, 'stp', 'Performing step 1.')
        console.start_animate(inline_spinner=True)
        time.sleep(1.2)
        console.sprint(1, 'wrn', 'A warning occurred in Step 1.')
        console.sprint(1, 'stp', 'Performing step 2.')
        console.start_animate(inline_spinner=True)
        time.sleep(1.1)        
        console.sprint(1, 'err', 'Step 2 failed. An error occurred.',)
        console.sprint(1, 'stp', 'Performing step 3.')
        console.start_animate(inline_spinner=True)
        time.sleep(1.4)        
        console.sprint(1, 'cmp', 'Step 3 completed.')
        time.sleep(2)
        print("-" * 40)
        console.sprint(0, 'str', 'Starting demo process. (spinner inline/replace)')
        console.sprint(1, 'stp', 'Performing step 1')
        console.start_animate(inline_spinner=True)
        time.sleep(1.1)
        console.sprint(1, 'wrn', 'A warning occurred in Step 1.',replace=True)
        console.sprint(1, 'stp', 'Performing step 2')
        console.start_animate(inline_spinner=True)
        time.sleep(1.7)        
        console.sprint(1, 'err', 'Step 2 failed. An error occurred.',replace=True)
        console.sprint(1, 'stp', 'Performing step 3')
        console.start_animate(inline_spinner=True)
        time.sleep(1.1)        
        console.sprint(1, 'cmp', 'Step 3 completed.',replace=True)
        time.sleep(2)        


if __name__ == "__main__":
    main()