import time
import consolio 

# Initialize Consolio with different spinner types
console_default = consolio.Consolio(spinner_type="default")
console_dots = consolio.Consolio(spinner_type="dots")
console_braille = consolio.Consolio(spinner_type="braille")

# 1. Demonstrating sprint steps with different statuses
print("Demonstrating sprint steps with various statuses:")
console_default.sprint(1, "str", "Start process...")
time.sleep(1)
console_default.sprint(1, "stp", "Step of a process...")
time.sleep(1)
console_default.sprint(1, "wrn", "Warning: Proceed with caution.")
time.sleep(1)
console_default.sprint(1, "err", "Error encountered!")
time.sleep(1)
console_default.sprint(1, "cmp", "Process completed successfully!")
time.sleep(1)

# 2. Demonstrating indentation levels
print("\nDemonstrating indentation levels:")
for indent_level in range(4):
    console_default.sprint(indent_level, "str", f"Indented message at level {indent_level}")
    time.sleep(0.5)

# 3. Demonstrating different spinners
print("\nDemonstrating different spinners:")
console_default.start_animate(indent=1)
time.sleep(2)
console_default.stop_animate()

console_dots.start_animate(indent=2)
time.sleep(2)
console_dots.stop_animate()

console_braille.start_animate(indent=3)
time.sleep(2)
console_braille.stop_animate()

# 4. Demonstrating various presentation modes
print("\nDemonstrating presentation modes:")

# Inline spinner mode
print("Inline spinner mode:")
console_default.sprint(1, "str", "Inline spinner running...", replace=True)
console_default.start_animate(inline_spinner=True)
time.sleep(3)
console_default.stop_animate()

# Inline spinner mode
print("Showing progress:")
console_braille.sprint(1, "str", "A process that requires progress disply...", replace=True)
console_braille.start_progress(indent=1)
for i in range(1,100):
    console_braille.update_progress(i)
    time.sleep(0.05)
console_braille.sprint(1,"cmp","The process finished.")

# Replacing previous line mode
print("\nReplacing previous line mode:")
console_default.sprint(1, "str", "This message will be replaced.")
time.sleep(2)
console_default.sprint(1, "cmp", "Message replaced successfully!", replace=True)


# Replacing previous line mode
print("\nMulti-line text (long text)")
console_default.sprint(1, "str", "This message is a really long message with inline spinner that will be replaced in 2 seconds. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.")
console_default.start_animate(inline_spinner=True)
time.sleep(2)
console_default.sprint(1, "cmp", "Message replaced successfully!", replace=True)
time.sleep(1)
console_default.sprint(1, "str", "This message is a really long message with normal spinner that will be replaced in 2 seconds. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.")
console_default.start_animate()
time.sleep(2)
console_default.sprint(1, "cmp", "Message replaced successfully!", replace=True)
print("\nDemonstration complete!")
