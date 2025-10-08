# Consolio

[![PyPI - Version](https://img.shields.io/pypi/v/consolio?style=for-the-badge)](https://pypi.org/project/consolio)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/consolio?style=for-the-badge)
![GitHub License](https://img.shields.io/github/license/devcoons/consolio?style=for-the-badge)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/consolio?style=for-the-badge&color=%23F0F)

`Consolio` is a lightweight, dependency-free Python library that provides an elegant way to display progress updates, warnings, errors, and other status messages in the console with color-coded indicators, spinners, and progress bars.

Perfect for CLI tools that need clean, structured feedback without complex dependencies.

---

## Installation

Consolio has **no external dependencies** and works out of the box.

```bash
pip install consolio
```

If you’re using it directly from source (e.g., cloned repository), add the `src/` folder to your `PYTHONPATH` or `sys.path`:

```python
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
from consolio import Consolio
```

---

## Features

- ✅ Color-coded messages for info, warning, error, success, and more.  
- 🔁 Built-in progress **spinners** (`dots`, `braille`, `default`).  
- 📈 Context-managed **progress bars**.  
- 🧩 Thread-safe and clean terminal rendering (no output corruption).  
- ⚙️ Works gracefully in both **TTY** and **non-TTY** (plain/CI) modes.  
- 🔄 Indentation helpers (`increase_indent`, `decrease_indent`, etc.) for hierarchical output.  

---

## Basic Usage

```python
from consolio import Consolio

console = Consolio(spinner_type='dots')

console.print("inf", "Starting process")
console.print("wip", "Loading configuration...")
console.print("wrn", "Warning: Low memory detected")
console.print("err", "Error: Invalid input detected")
console.print("cmp", "All done!")
```

---

## Indentation Control

You can now manage indentation dynamically without passing it every time.

```python
console.increase_indent()
console.print("wip", "Setting up environment...")

console.increase_indent()
console.print("inf", "Fetching dependencies...")

console.decrease_indent()
console.print("cmp", "Setup complete.")
```

Explicit indentation still works:

```python
console.print(2, "inf", "Manual indentation works too.")
```

---

## Spinners

Use the spinner as a **context manager**:

```python
import time

with console.spinner("Working hard...", inline=True):
    time.sleep(2)

console.print("cmp", "Task complete!")
```

Or manually start and stop it:

```python
console.start_animate()
time.sleep(3)
console.stop_animate()
```

---

## Progress Bars

```python
import time

with console.progress(initial_percentage=0) as update:
    for i in range(0, 101, 20):
        time.sleep(0.3)
        update(i)

console.print("cmp", "Progress complete!")
```

---

## Input Handling

```python
user = console.input("qst", "Enter your name:")
console.print("cmp", f"Hello, {user}!")
```

---

##  Customization

| Option | Description | Example |
|---------|-------------|----------|
| `spinner_type` | Type of spinner (`dots`, `braille`, `default`) | `Consolio(spinner_type='braille')` |
| `no_colors` | Disable ANSI colors | `Consolio(no_colors=True)` |
| `no_animation` | Disable spinners/progress bars | `Consolio(no_animation=True)` |
| `replace=True` | Overwrite previous message line | `console.print("inf", "Updating...", replace=True)` |
| `plain()` | Force plain output (no color/animation) | `console.plain()` |
| `rich()` | Re-enable color/animation if supported | `console.rich()` |


## Example Structure

Example scripts are located in the [`examples/`](examples/) folder:
- `example_basic_usage.py` — Interactive demo with spinner and progress bar.  
- `example_plain_mode.py` — CI-friendly non-interactive demo.

Run them directly:

```bash
python examples/example_basic_usage.py
```


## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

Made with ❤️ by [devcoons](https://github.com/devcoons)
