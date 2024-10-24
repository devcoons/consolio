import threading
import time

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

    def __init__(self):
        self._animating = False
        self._spinner_thread = None
        self._lock = threading.Lock()

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
        spinner_chars = '|/-\\'
        idx = 0
        indent_spaces = " " * (indent * 4)
        while self._animating:
            spinner_char = spinner_chars[idx % len(spinner_chars)]
            line = f"{indent_spaces} {self.FG_MG}{spinner_char}{self.RESET}"
            with self._lock:
                print(line, end='\r', flush=True)
            time.sleep(0.1)
            idx += 1
        with self._lock:
            print(' ' * len(line), end='\r', flush=True)

    def stop_animate(self):
        if self._animating:
            self._animating = False
            self._spinner_thread.join()
            self._spinner_thread = None


