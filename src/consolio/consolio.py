import threading
import shutil
import time
import sys
import os

class ConsolioUtils:

    def get_terminal_size():
        size = shutil.get_terminal_size(fallback=(80, 24))
        return [size.columns, size.lines]

    def split_text_to_fit(text,  indent=0): 
        effective_width = (ConsolioUtils.get_terminal_size()[0]-2) - indent
        lines = []      
        while text:     
            line = text[:effective_width]
            lines.append(line.strip())
            text = text[effective_width:]       
        return lines


class Consolio:

    FG_RD = "\033[31m"    # Red (error)
    FG_GR = "\033[32m"    # Green (success)
    FG_YW = "\033[33m"    # Yellow (warning)
    FG_CB = "\033[36m"    # Cyan (step)
    FG_BL = "\033[34m"    # Blue (start)
    FG_MG = "\033[35m"    # Magenta (spinner)
    RESET = "\033[0m"     # Reset

    PROG_BEG = FG_BL + '[+] ' + RESET  # Start
    PROG_STP = FG_CB + '[-] ' + RESET  # Step
    PROG_WRN = FG_YW + '[!] ' + RESET  # Warning
    PROG_ERR = FG_RD + '[x] ' + RESET  # Error
    PROG_CMP = FG_GR + '[v] ' + RESET  # Complete

    SPINNERS = {
        'dots':  ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷'],
        'braille': ['⠋', '⠙', '⠚', '⠞', '⠖', '⠦', '⠴', '⠲', '⠳', '⠓'],
        'default': ['|', '/', '-', '\\']
    }

    _last_message = []
    _last_indent = 0

    def __init__(self, spinner_type='default'):
        self._animating = False
        self._spinner_thread = None
        self._lock = threading.Lock()
        self._last_message = []

        self.spinner_type = spinner_type.lower()
        self.spinner_chars = self.SPINNERS.get(self.spinner_type, self.SPINNERS['default'])

        # Check if the spinner is supported
        if not self.is_spinner_supported(self.spinner_chars):
            self.spinner_type = 'default'
            self.spinner_chars = self.SPINNERS['default']

    def sprint(self, indent, status, text, replace = False):
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
            if replace == True:
                total_indent = len(indent_spaces)+4
                total_indent_spaces = " " * (total_indent)
                text_lines = ConsolioUtils.split_text_to_fit(self._last_text,total_indent)[::-1]
                empty_space =  " " * (total_indent+(len(text_lines[0])))
                print("\033[F"+empty_space, end='\r')
                for ln in text_lines[1:]:
                    empty_space =  " " * (total_indent+(len(ln)))              
                    print("\033[F"+empty_space, end='\r')
            self._last_status_prefix = status_prefix
            self._last_indent = indent
            self._last_text = text
            total_indent = len(indent_spaces)+4
            total_indent_spaces = " " * (total_indent)
            text_lines = ConsolioUtils.split_text_to_fit(text,total_indent)
            print(f"{indent_spaces}{status_prefix}{text_lines[0]}")
            for ln in text_lines[1:]:
                print(f"{total_indent_spaces}{ln}")

    def start_animate(self, indent=0, inline_spinner=False):
        if self._animating:
            return
        self._animating = True
        self._spinner_thread = threading.Thread(target=self._animate, args=(indent, inline_spinner))
        self._spinner_thread.start()

    def _animate(self, indent, inline_spinner):
        idx = 0
        print("\033[?25l", end="")
        spinner_position = 4 + (self._last_indent * 4)
        try:
            while self._animating:
                spinner_char = self.spinner_chars[idx % len(self.spinner_chars)]
                if inline_spinner:
                    # Inline spinner mode: Move cursor up and replace previous line
                    with self._lock:
                        indent_spaces = " " * (self._last_indent * 4)
                        text_lines = ConsolioUtils.split_text_to_fit(self._last_text,len(indent_spaces)+4)
                        tline = f"{indent_spaces}{self._last_status_prefix[:5]}[{self.FG_MG}{spinner_char}{self._last_status_prefix[:5]}]{self.RESET} {text_lines[0]}"
                        line = ("\033[F" * len(text_lines))+tline+("\033[B" * len(text_lines))
                        print(line,end="",flush=True)
                else:
                    # Regular spinner animation on a new line
                    indent_spaces = " " * (indent * 4)
                    with self._lock:
                        line = f"{indent_spaces} {self.FG_MG}{spinner_char}{self.RESET}"
                        clear_line = line
                        print(f"{clear_line}", end='\r', flush=True)
                time.sleep(0.1)
                idx += 1
                
        finally:
            print("\033[?25h", end="")
            if not inline_spinner:
                clear_line = ' ' * len(line)
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
