import threading
import time
import sys
import os

class Consolio:
    # Color definitions
    FG_RD = "\033[31m"    # Red (error)
    FG_GR = "\033[32m"    # Green (success)
    FG_YW = "\033[33m"    # Yellow (warning)
    FG_CB = "\033[36m"    # Cyan (step)
    FG_BL = "\033[34m"    # Blue (start)
    FG_MG = "\033[35m"    # Magenta (spinner)
    RESET = "\033[0m"     # Reset

    # Status tags
    PROG_BEG = FG_BL + '[+] ' + RESET  # Start
    PROG_STP = FG_CB + '[-] ' + RESET  # Step
    PROG_WRN = FG_YW + '[!] ' + RESET  # Warning
    PROG_ERR = FG_RD + '[x] ' + RESET  # Error
    PROG_CMP = FG_GR + '[v] ' + RESET  # Complete

    # Spinner definitions
    SPINNERS = {
        'star':  ['✶', '✸', '✹', '✺', '✹', '✷'],
        'moon':  ['🌑', '🌒', '🌓', '🌔', '🌕', '🌖', '🌗', '🌘'],
        'snake': ['⠋', '⠙', '⠚', '⠞', '⠖', '⠦', '⠴', '⠲', '⠳', '⠓'],
        'default': ['|', '/', '-', '\\']
    }

    def __init__(self, spinner_type='default'):
        self._animating = False
        self._spinner_thread = None
        self._lock = threading.Lock()

        # Store the selected spinner type
        self.spinner_type = spinner_type.lower()
        self.spinner_chars = self.SPINNERS.get(self.spinner_type, self.SPINNERS['default'])

        # Check if the spinner is supported
        if not self.is_spinner_supported(self.spinner_chars):
            self.spinner_type = 'default'
            self.spinner_chars = self.SPINNERS['default']

    def sprint(self, indent, status, text):
        self.stop_animate()
        status_prefix = {
            "str": self.PROG_BEG,
            "stp": self.PROG_STP,
            "wrn": self.PROG_WRN,
            "err": self.PROG_ERR,
            "cmp": self.PROG_CMP
        }.get(status, "")
        indent_spaces = " " * (indent * 4)
        with self._lock:
            print(f"{indent_spaces}{status_prefix}{text}")

    def start_animate(self, indent=0):
        if self._animating:
            return
        self._animating = True
        self._spinner_thread = threading.Thread(target=self._animate, args=(indent,))
        self._spinner_thread.start()

    def _animate(self, indent):
        idx = 0
        indent_spaces = " " * (indent * 4)
        while self._animating:
            spinner_char = self.spinner_chars[idx % len(self.spinner_chars)]
            line = f"{indent_spaces} {self.FG_MG}{spinner_char}{self.RESET}"
            with self._lock:
                print(line, end='\r', flush=True)
            time.sleep(0.1)
            idx += 1
        with self._lock:
            clear_line = ' ' * (len(line))
            print(f"{clear_line}", end='\r', flush=True)

    def stop_animate(self):
        if self._animating:
            self._animating = False
            self._spinner_thread.join()
            self._spinner_thread = None

    def is_spinner_supported(self, spinner_chars):
        encoding = sys.stdout.encoding or 'utf-8'
        for char in spinner_chars:
            try:
                char.encode(encoding)
            except UnicodeEncodeError:
                return False
            except Exception:
                return False
        return True
