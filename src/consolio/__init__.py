#########################################################################################
#                                                                                       #
# MIT License                                                                           #
#                                                                                       #
# Copyright (c) 2024 Ioannis D. (devcoons)                                              #
#                                                                                       #
# Permission is hereby granted, free of charge, to any person obtaining a copy          #
# of this software and associated documentation files (the "Software"), to deal         #
# in the Software without restriction, including without limitation the rights          #
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell             #
# copies of the Software, and to permit persons to whom the Software is                 #
# furnished to do so, subject to the following conditions:                              #
#                                                                                       #
# The above copyright notice and this permission notice shall be included in all        #
# copies or substantial portions of the Software.                                       #
#                                                                                       #
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR            #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,              #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE           #
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER                #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,         #
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE         #
# SOFTWARE.                                                                             #
#                                                                                       #
#########################################################################################

from __future__ import annotations

__version__ = '0.1.15'
__name__ = "consolio"
__all__ = ['Consolio','ConsolioUtils']

import os
import sys
import time
import threading
import platform
import getpass
import shutil
from contextlib import contextmanager
from typing import Iterable, List, Literal, Optional

# --------------------------------------------------------------------------------------
# Utils
# --------------------------------------------------------------------------------------

class ConsolioUtils:
    """Utility functions for terminal operations and text formatting."""

    @staticmethod
    def get_terminal_size() -> List[int]:
        size = shutil.get_terminal_size(fallback=(80, 24))
        return [size.columns, size.lines]

    @staticmethod
    def split_text_to_fit(text: str, indent: int = 0) -> list[str]:
        effective_width = ((ConsolioUtils.get_terminal_size()[0] - 2) - indent) if sys.stdout.isatty() else 512
        lines: list[str] = []
        segments = text.split("\n")
        for seg in segments:
            if seg == "":
                lines.append("")
                continue
            t = seg
            while t:
                line = t[:effective_width]
                if len(t) > effective_width and " " in line:
                    space_idx = line.rfind(" ")
                    line = t[:space_idx]
                    t = t[space_idx + 1 :]
                else:
                    t = t[effective_width:]
                lines.append(line.rstrip())
        return lines if lines else [""]

    @staticmethod
    def detect_os() -> str:
        system = platform.system()
        if system == "Windows":
            return "windows"
        elif system == "Linux":
            return "linux"
        elif system == "Darwin":
            return "mac"
        else:
            return system.lower()

# --------------------------------------------------------------------------------------
# Main class
# --------------------------------------------------------------------------------------

Status = Literal["inf", "wip", "wrn", "err", "cmp", "qst"]

class Consolio:
    """Terminal printing with color-coded messages, spinner and progress.

    Key behavior changes vs original:
    - Fixes Linux animation support (enabled on TTY).
    - Honors NO_COLOR / FORCE_COLOR / CI and non-TTY.
    - Adds context-manager spinner/progress that guarantee cleanup.
    - Makes question prefix color-aware.
    - Removes process-wide signal handlers (library should not own them).
    - Thread-safe prints via a single internal lock.
    """

    FG_RD = "\033[31m"; FG_GR = "\033[32m"; FG_YW = "\033[33m"; FG_CB = "\033[36m"; FG_BL = "\033[34m"; FG_MG = "\033[35m"; FG_BB = "\033[94m"; RESET = "\033[0m"

    PROG_INF = ["[i] ", FG_BL + "[i] " + RESET]
    PROG_WIP = ["[-] ", FG_CB + "[-] " + RESET]
    PROG_WRN = ["[!] ", FG_YW + "[!] " + RESET]
    PROG_ERR = ["[x] ", FG_RD + "[x] " + RESET]
    PROG_CMP = ["[v] ", FG_GR + "[v] " + RESET]
    PROG_QST = ["[?] ", FG_BB + "[?] " + RESET]

    SPINNERS = {
        "dots": ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"],
        "braille": ["⠋", "⠙", "⠚", "⠞", "⠖", "⠦", "⠴", "⠲", "⠳", "⠓"],
        "default": ["|", "/", "-", "\\"],
    }

    # ----------------------------------------------------------------------------------

    def __init__(self, spinner_type: str = "default", no_colors: bool = False, no_animation: bool = False) -> None:
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._animating = False
        self._progressing = False
        self._spinner_thread: Optional[threading.Thread] = None
        self._progress_thread: Optional[threading.Thread] = None
        self._last_message: List[str] = []
        self._last_indent = 0
        self._last_text = ""
        self._last_text_lines: List[str] = []
        self._last_status_prefix = ""
        self.spinner_type = spinner_type.lower()
        self.spinner_chars = self.SPINNERS.get(self.spinner_type, self.SPINNERS["default"])
        self.current_progress = 0
        self._suspend = False
 
        self._enabled_colors = False if no_colors else self.is_color_supported()
        self._enabled_spinner = False if no_animation else self.is_animation_supported()
        if not self.is_spinner_supported(self.spinner_chars):
            self.spinner_type = "default"
            self.spinner_chars = self.SPINNERS["default"]

        self._status_prefixes = {
            "inf": self.PROG_INF[0 if not self._enabled_colors else 1],
            "wip": self.PROG_WIP[0 if not self._enabled_colors else 1],
            "wrn": self.PROG_WRN[0 if not self._enabled_colors else 1],
            "err": self.PROG_ERR[0 if not self._enabled_colors else 1],
            "cmp": self.PROG_CMP[0 if not self._enabled_colors else 1],
            "qst": self.PROG_QST[0 if not self._enabled_colors else 1],
        }

    # ----------------------------------------------------------------------------------
    # Capability detection

    def set_indent(self, level: int) -> None:
        with self._lock:
            self._last_indent = max(0, int(level))

    def reset_indent(self) -> None:
        self.set_indent(0)

    def increase_indent(self, step: int = 1) -> None:
        with self._lock:
            self._last_indent = max(0, self._last_indent + int(step))

    def decrease_indent(self, step: int = 1) -> None:
        with self._lock:
            self._last_indent = max(0, self._last_indent - int(step))

    def is_animation_supported(self) -> bool:
        if os.environ.get("CI"):
            return False
        if not sys.stdout.isatty():
            return False
        which_os = ConsolioUtils.detect_os()
        if which_os == "windows":
            # Windows 10 build >= 19041 is generally OK for ANSI and live updates in modern terminals
            try:
                build = int(platform.version().split(".")[2])
            except Exception:
                build = 0
            return build >= 19000 or "WT_SESSION" in os.environ or os.environ.get("TERM_PROGRAM") == "vscode"
        # Linux and macOS: assume modern terminals can animate
        return True

    def is_color_supported(self) -> bool:
        if os.environ.get("NO_COLOR"):
            return False
        if os.environ.get("FORCE_COLOR"):
            return True
        if not sys.stdout.isatty():
            return False
        which_os = ConsolioUtils.detect_os()
        if which_os == "windows":
            try:
                build = int(platform.version().split(".")[2])
            except Exception:
                build = 0
            if build >= 19000 or "WT_SESSION" in os.environ or os.environ.get("TERM_PROGRAM") == "vscode" or "ANSICON" in os.environ or "ConEmuANSI" in os.environ:
                return True
            return False
        term = os.environ.get("TERM", "")
        if term in ("xterm", "xterm-color", "xterm-256color", "screen", "screen-256color", "linux", "vt100"):
            return True
        return "COLORTERM" in os.environ

    def is_spinner_supported(self, spinner_chars: Iterable[str]) -> bool:
        encoding = sys.stdout.encoding or "utf-8"
        try:
            for ch in spinner_chars:
                ch.encode(encoding)
        except Exception:
            return False
        return True

    # ----------------------------------------------------------------------------------
    # Public controls

    def suspend(self) -> None:
        with self._lock:
            self.stop_progress()
            self.stop_animate()
            self._suspend = True

    def resume(self) -> None:
        with self._lock:
            self._suspend = False

    def plain(self) -> None:
        with self._lock:
            self.stop_animate()
            self.stop_progress()
            self._enabled_spinner = False
            self._enabled_colors = False
            self._refresh_prefixes()

    def rich(self) -> None:
        with self._lock:
            self._enabled_spinner = self.is_animation_supported()
            self._enabled_colors = self.is_color_supported()
            self._refresh_prefixes()

    def _refresh_prefixes(self) -> None:
        self._status_prefixes.update({
            k: ([self.PROG_INF, self.PROG_WIP, self.PROG_WRN, self.PROG_ERR, self.PROG_CMP, self.PROG_QST][idx][0 if not self._enabled_colors else 1])
            for idx, k in enumerate(["inf", "wip", "wrn", "err", "cmp", "qst"])
        })

    # ----------------------------------------------------------------------------------
    # Printing and input

    def print(self, *args: object, replace: bool = False) -> None:
        """
        Signatures:
        - print(text)
        - print(status, text)
        - print(indent, status, text)
        """
        if len(args) == 1:
            indent = self._last_indent
            status: Status = "inf"
            text = str(args[0])
        elif len(args) == 2:
            indent = self._last_indent
            status, text = args  
            status = self._validate_status(status)
            text = str(text)
        elif len(args) == 3:
            indent, status, text = args 
            indent = int(indent)
            status = self._validate_status(status)
            text = str(text)
        else:
            raise TypeError("print() takes 1, 2 or 3 positional arguments")

        if self._suspend:
            return

        self.stop_animate()
        self.stop_progress()

        status_prefix = self._status_prefixes.get(status, "")
        indent_spaces = " " * (indent * 4)

        with self._lock:
            if replace and sys.stdout.isatty():
                total_indent = (self._last_indent * 4) + 4
                for ln in reversed(ConsolioUtils.split_text_to_fit(self._last_text, total_indent)):
                    print(f"\033[F{' ' * (total_indent + len(ln))}", end="\r")

            self._last_status_prefix = status_prefix
            self._last_indent = indent
            self._last_text = text
            total_indent = len(indent_spaces) + 4
            total_indent_spaces = " " * total_indent
            text_lines = ConsolioUtils.split_text_to_fit(text, total_indent)

            rvar = "\r" if sys.stdout.isatty() else ""
            print(f"{rvar}{indent_spaces}{status_prefix}{text_lines[0]}")
            for ln in text_lines[1:]:
                print(f"{rvar}{total_indent_spaces}{ln}")

    def input(self, indent: int, question: str, *, inline: bool = False, hidden: bool = False, replace: bool = False) -> str:
        if self._suspend:
            return ""
        
        
        self.stop_animate(); self.stop_progress()
        indent_spaces = " " * (indent * 4)

        if replace and sys.stdout.isatty():
            total_indent = (self._last_indent * 4) + 4
            for ln in reversed(ConsolioUtils.split_text_to_fit(self._last_text, total_indent)):
                print(f"\033[F{' ' * (total_indent + len(ln))}", end="\r")

        status_prefix = self._status_prefixes["qst"]
        total_indent = len(indent_spaces) + 4
        total_indent_spaces = " " * total_indent
        text_lines = ConsolioUtils.split_text_to_fit(question, total_indent)

        print(f"{indent_spaces}{status_prefix}{text_lines[0]}", end="")
        for ln in text_lines[1:]:
            print(f"\n{total_indent_spaces}{ln}", end="")

        if hidden:
            if inline:
                user_input = getpass.getpass(" ")
                self._last_text = question + "#"
            else:
                print()
                user_input = getpass.getpass(total_indent_spaces)
                self._last_text = question + ("#" * (ConsolioUtils.get_terminal_size()[0] - 2))
        else:
            if inline:
                user_input = input(" ")
                self._last_text = question + "#" + ("#" * len(user_input))
            else:
                print()
                user_input = input(total_indent_spaces)
                extra_space = (ConsolioUtils.get_terminal_size()[0] - 2) + len(user_input)
                self._last_text = question + ("#" * extra_space)
        self._last_status_prefix = status_prefix
        self._last_indent = indent
        return user_input

    # ----------------------------------------------------------------------------------
    # Spinner (context manager preferred)

    @contextmanager
    def spinner(self, text: Optional[str] = None, *, indent: int = 0, inline: bool = False):
        """Context manager spinner that always tears down correctly."""
        if text:
            self.print(indent, "wip", text)
        self.start_animate(indent=indent, inline_spinner=inline)
        try:
            yield
        finally:
            self.stop_animate()

    def start_animate(self, indent: int = 0, inline_spinner: bool = False) -> None:
        if self._suspend or not self._enabled_spinner or self._animating:
            return
        with self._lock:
            self._stop_event = threading.Event()
            self._animating = True
            self._spinner_thread = threading.Thread(target=self._animate, args=(indent, inline_spinner), daemon=True)
            self._spinner_thread.start()

    def _animate(self, indent: int, inline_spinner: bool) -> None:
        if self._suspend or not self._enabled_spinner:
            return
        idx = 0
        try:
            with self._lock:
                if sys.stdout.isatty():
                    print("\033[?25l", end="", flush=True) 
            while True:
                with self._lock:
                    if not self._animating or self._stop_event.is_set():
                        break
                spinner_char = self.spinner_chars[idx % len(self.spinner_chars)]
                if inline_spinner:
                    with self._lock:
                        indent_spaces = " " * (self._last_indent * 4)
                        text_lines = ConsolioUtils.split_text_to_fit(self._last_text, len(indent_spaces) + 4)
                        if not self._enabled_colors:
                            tline = f"{indent_spaces}[{spinner_char}] {text_lines[0]}"
                        else:
                            tline = f"{indent_spaces}{self.FG_BL}[{self.FG_MG}{spinner_char}{self.FG_BL}]{self.RESET} {text_lines[0]}"
                        line = ("\033[F" * max(1, len(text_lines))) + tline + ("\033[B" * max(1, len(text_lines)))
                        print(line, end="", flush=True)
                else:
                    indent_spaces = " " * (indent * 4)
                    with self._lock:
                        if not self._enabled_colors:
                            line = f"{indent_spaces} {spinner_char}"
                        else:
                            line = f"{indent_spaces} {self.FG_MG}{spinner_char}{self.RESET}"
                        print(f"{line}", end="\r", flush=True)
                time.sleep(0.1)
                idx += 1
        finally:
            with self._lock:
                if sys.stdout.isatty():
                    print("\033[?25h", end="\r", flush=True) 
                if not inline_spinner:
                    print(" " * (ConsolioUtils.get_terminal_size()[0] - 1), end="\r", flush=True)

    def stop_animate(self) -> None:
        with self._lock:
            if not self._animating:
                return
            self._animating = False
            self._stop_event.set()
            t = self._spinner_thread
        if t is not None:
            t.join(timeout=2)
        with self._lock:
            self._spinner_thread = None

    # ----------------------------------------------------------------------------------
    # Progress (simple percentage indicator rendered with spinner engine)

    @contextmanager
    def progress(self, *, indent: Optional[int] = None, initial_percentage: int = 0):
        if indent is None:
            indent = self._last_indent        
        self.start_progress(indent=indent, initial_percentage=initial_percentage)
        try:
            yield self.update_progress
        finally:
            self.stop_progress()

    def start_progress(self, indent: Optional[int] = None, initial_percentage: int = 0) -> None:
        if self._suspend or not self._enabled_spinner:
            return
        if indent is None:
            indent = self._last_indent
        with self._lock:
            self.stop_animate()
            self.stop_progress()
            self._progressing = True
            self.current_progress = max(0, min(100, int(initial_percentage)))
            self._progress_thread = threading.Thread(target=self._progress, args=(indent,), daemon=True)
            self._progress_thread.start()

    def _progress(self, indent: int) -> None:
        if self._suspend or not self._enabled_spinner:
            return
        idx = 0
        while True:
            with self._lock:
                if not self._progressing or self._stop_event.is_set():
                    break
                spinner_char = self.spinner_chars[idx % len(self.spinner_chars)]
                indent_spaces = " " * (indent * 4)
                if not self._enabled_colors:
                    line = f"{indent_spaces}[{spinner_char}] In progress: {self.current_progress}%"
                else:
                    line = f"{indent_spaces}{self.FG_BL}[{self.FG_MG}{spinner_char}{self.FG_BL}]{self.RESET} In progress: {self.FG_YW}{self.current_progress}%{self.RESET}"
                print(f"{line}", end="\r", flush=True)
            time.sleep(0.1)
            idx += 1
        with self._lock:
            print(" " * (ConsolioUtils.get_terminal_size()[0] - 1), end="\r", flush=True)

    def update_progress(self, percentage: int) -> None:
        if self._suspend or not self._enabled_spinner:
            return
        with self._lock:
            self.current_progress = max(0, min(100, int(percentage)))

    def stop_progress(self) -> None:
        with self._lock:
            if not self._progressing:
                return
            self._progressing = False
            t = self._progress_thread
        if t is not None:
            t.join(timeout=2)
        with self._lock:
            self._progress_thread = None

    # ----------------------------------------------------------------------------------
    # Helpers

    def _validate_status(self, status: object) -> Status:
        s = str(status).lower()
        if s not in ("inf", "wip", "wrn", "err", "cmp", "qst"):
            raise ValueError(f"Unknown status '{status}'. Expected one of inf/wip/wrn/err/cmp/qst")
        return s 

    def enable_animation(self) -> None:
        self._enabled_spinner = self.is_animation_supported()

    def disable_animation(self) -> None:
        with self._lock:
            self.stop_animate()
            self._enabled_spinner = False

# --------------------------------------------------------------------------------------
# EOF
# --------------------------------------------------------------------------------------