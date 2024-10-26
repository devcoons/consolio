# Consolio

`Consolio` is a Python library that provides an elegant way to display progress updates, warnings, errors, and other status messages in the console with color-coded indicators and spinners. Ideal for CLI applications that require step-by-step feedback to users.

## Table of Contents

- [Installation](#installation)
- [Features](#features)
- [Usage](#usage)
  - [Basic Initialization](#basic-initialization)
  - [Status Message Types](#status-message-types)
  - [Spinners](#spinners)
- [Customization](#customization)

## Installation

Consolio does not require any dependencies outside of Python's standard library. To use it just install it using `pip install consolio`.

## Features

- Color-coded messages for different statuses: Success, Error, Warning, and more.
- Progress spinners in various styles (`dots`, `braille`, `default`).
- Inline spinners for seamless progress tracking within a single line.
- Thread-safe output for smooth and consistent console display.

## Usage

### Basic Initialization

To get started, initialize `Consolio` with a desired spinner type. You can choose from `dots`, `braille`, or `default`.

```
from consolio import Consolio

console = Consolio(spinner_type='dots')  # Initialize with dots spinner
```

### Status Message Types

Consolio supports multiple status messages, each with a unique color and symbol:

- **Start**: `[+]` Blue - Marks the start of a process
- **Step**: `[-]` Cyan - Intermediate step in a process
- **Warning**: `[!]` Yellow - Displays warnings
- **Error**: `[x]` Red - Displays errors
- **Complete**: `[v]` Green - Indicates completion of a step or process

Use the `sprint` method to print messages with a specific status, indentation level, and replacement option:

```
console.sprint(indent=0, status="str", text="Starting process")
console.sprint(indent=1, status="stp", text="Executing step 1")
console.sprint(indent=1, status="wrn", text="Warning: Check your input")
console.sprint(indent=1, status="err", text="Error: Process failed")
console.sprint(indent=0, status="cmp", text="Process complete")
```

### Spinners

You can start a spinner to indicate an ongoing process using the `start_animate` method, then stop it using `stop_animate`.

```
console.start_animate(indent=1)
# Perform a time-consuming task here
time.sleep(3)  # Simulating task duration
console.stop_animate()
```

Use the `inline_spinner=True` option to display the spinner on the same line as the last message:

```
console.sprint(1, "stp", "Calculating size")
console.start_animate(inline_spinner=True)
time.sleep(2)
console.stop_animate()
```
### Customization

The `Consolio` library supports a few customization options:

- **Spinner Type**: Set `spinner_type` to `dots`, `braille`, or `default`.
- **Indentation Level**: Control indentation level in messages for organized output.
- **Inline Spinner**: Use `inline_spinner=True` to keep spinners on the same line as a message.
- **Replacement Mode**: Set `replace=True` in `sprint` to overwrite the previous message line.

