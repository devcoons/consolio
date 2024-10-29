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

#########################################################################################
# IMPORTS                                                                               #
#########################################################################################

import threading
import getpass
import shutil
import time
import sys
import os

#########################################################################################
# CLASS: ConsolioUtils                                                                  #
#########################################################################################

class ConsolioUtils:
    """Utility functions for terminal operations and text formatting."""
    
    # --------------------------------------------------------------------------------- #

    def get_terminal_size():
        size = shutil.get_terminal_size(fallback=(80, 24))
        return [size.columns, size.lines]

    # --------------------------------------------------------------------------------- #

    def split_text_to_fit(text, indent=0): 
        effective_width = (ConsolioUtils.get_terminal_size()[0] - 2) - indent
        lines = []      
        while text:     
            line = text[:effective_width]
            lines.append(line.strip())
            text = text[effective_width:]       
        return lines


#########################################################################################
# CLASS: Consolio                                                                      #
#########################################################################################

class Consolio:
    """Main class for terminal printing with color-coded messages and animations."""
    
    # --------------------------------------------------------------------------------- #

    FG_RD = "\033[31m"    
    FG_GR = "\033[32m"    
    FG_YW = "\033[33m"  
    FG_CB = "\033[36m"    
    FG_BL = "\033[34m"    
    FG_MG = "\033[35m" 
    FG_BB = "\033[94m"   
    RESET = "\033[0m"     

    PROG_INF = FG_BL + '[i] ' + RESET
    PROG_WIP = FG_CB + '[-] ' + RESET
    PROG_WRN = FG_YW + '[!] ' + RESET
    PROG_ERR = FG_RD + '[x] ' + RESET
    PROG_CMP = FG_GR + '[v] ' + RESET
    PROG_QST = FG_BB + '[?] ' + RESET

    SPINNERS = {
        'dots':  ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷'],
        'braille': ['⠋', '⠙', '⠚', '⠞', '⠖', '⠦', '⠴', '⠲', '⠳', '⠓'],
        'default': ['|', '/', '-', '\\']
    }

    _last_message = []
    _last_indent = 0

    # --------------------------------------------------------------------------------- #
    # --------------------------------------------------------------------------------- #

    def __init__(self, spinner_type='default'):
        self._animating = False
        self._progressing = False
        self._spinner_thread = None
        self._progress_thread = None
        self._lock = threading.Lock()
        self._last_message = []
        self.spinner_type = spinner_type.lower()
        self.spinner_chars = self.SPINNERS.get(self.spinner_type, self.SPINNERS['default'])
        self.current_progress = 0

        if not self.is_spinner_supported(self.spinner_chars):
            self.spinner_type = 'default'
            self.spinner_chars = self.SPINNERS['default']

    # --------------------------------------------------------------------------------- #

    def start_progress(self, indent=0, initial_percentage=0):
        self.stop_animate()
        self.stop_progress()
        self._progressing = True
        self.current_progress = initial_percentage
        self._progress_thread = threading.Thread(target=self._progress, args=(indent,))
        self._progress_thread.start()

    # --------------------------------------------------------------------------------- #

    def _progress(self, indent):
        idx = 0
        spinner_position = 4 + (self._last_indent * 4)
        while self._progressing:
            spinner_char = self.spinner_chars[idx % len(self.spinner_chars)]
            indent_spaces = " " * (indent * 4)
            with self._lock:
                line = f"{indent_spaces}{self.FG_BL}[{self.FG_MG}{spinner_char}{self.FG_BL}]{self.RESET} In progress: {self.FG_YW}{self.current_progress}%{self.RESET}"
                print(f"{line}", end='\r', flush=True)
            time.sleep(0.1)
            idx += 1
        print(' ' * len(line), end='\r', flush=True) 

    # --------------------------------------------------------------------------------- #

    def update_progress(self, percentage):
        with self._lock:
            self.current_progress = percentage

    # --------------------------------------------------------------------------------- #

    def stop_progress(self):
        if self._progressing:
            self._progressing = False
            self._progress_thread.join()
            self._progress_thread = None

    # --------------------------------------------------------------------------------- #
    
    def input(self, indent, question, inline=False, hidden=False, replace=False):
        self.stop_animate()
        self.stop_progress()
        indent_spaces = " " * (indent * 4)
        
        if replace:
            total_indent = len(indent_spaces) + 4
            total_indent_spaces = " " * total_indent
            text_lines = ConsolioUtils.split_text_to_fit(self._last_text, total_indent)[::-1]
            for ln in text_lines:
                print(f"\033[F{' ' * (total_indent + len(ln))}", end='\r')
                
        status_prefix = self.PROG_QST
        total_indent = len(indent_spaces) + 4
        total_indent_spaces = " " * total_indent
        text_lines = ConsolioUtils.split_text_to_fit(question, total_indent)
        
        print(f"{indent_spaces}{status_prefix}{text_lines[0]}", end='')
        for ln in text_lines[1:]:
            print(f"\n{total_indent_spaces}{ln}", end='')

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
                self._last_text = question + "#" +("#" * len(user_input))
            else:
                print()
                user_input = input(total_indent_spaces)
                extra_space = (ConsolioUtils.get_terminal_size()[0] - 2) + len(user_input)
                self._last_text = question + ("#" * extra_space)
        self._last_status_prefix = self.PROG_QST
        self._last_indent = indent
        
        return user_input

    # --------------------------------------------------------------------------------- #

    def print(self, indent, status, text, replace=False):
        self.stop_animate()
        self.stop_progress()
        status_prefix = {
            "inf": self.PROG_INF,
            "wip": self.PROG_WIP,
            "wrn": self.PROG_WRN,
            "err": self.PROG_ERR,
            "cmp": self.PROG_CMP
        }.get(status, "")
        indent_spaces = " " * (indent * 4)
        
        with self._lock:
            if replace:
                total_indent = (self._last_indent*4) + 4
                total_indent_spaces = " " * total_indent
                text_lines = ConsolioUtils.split_text_to_fit(self._last_text, total_indent)[::-1]
                
                for ln in text_lines:
                    print(f"\033[F{' ' * (total_indent + len(ln))}", end='\r')
                    
            self._last_status_prefix = status_prefix
            self._last_indent = indent
            self._last_text = text
            total_indent = len(indent_spaces) + 4
            total_indent_spaces = " " * total_indent
            text_lines = ConsolioUtils.split_text_to_fit(text, total_indent)
            
            print(f"\r{indent_spaces}{status_prefix}{text_lines[0]}")
            for ln in text_lines[1:]:
                print(f"\r{total_indent_spaces}{ln}")

    # --------------------------------------------------------------------------------- #

    def start_animate(self, indent=0, inline_spinner=False):
        self.stop_progress()
        if self._animating:
            return
        self._animating = True
        self._spinner_thread = threading.Thread(target=self._animate, args=(indent, inline_spinner))
        self._spinner_thread.start()

    # --------------------------------------------------------------------------------- #

    def _animate(self, indent, inline_spinner):
        idx = 0
        print("\033[?25l", end="")
        spinner_position = 4 + (self._last_indent * 4)
        
        try:
            while self._animating:
                spinner_char = self.spinner_chars[idx % len(self.spinner_chars)]
                
                if inline_spinner:
                    with self._lock:
                        indent_spaces = " " * (self._last_indent * 4)
                        text_lines = ConsolioUtils.split_text_to_fit(self._last_text, len(indent_spaces) + 4)
                        tline = f"{indent_spaces}{self._last_status_prefix[:5]}[{self.FG_MG}{spinner_char}{self._last_status_prefix[:5]}]{self.RESET} {text_lines[0]}"
                        line = ("\033[F" * len(text_lines)) + tline + ("\033[B" * len(text_lines))
                        print(line, end="", flush=True)
                else:
                    indent_spaces = " " * (indent * 4)
                    with self._lock:
                        line = f"{indent_spaces} {self.FG_MG}{spinner_char}{self.RESET}"
                        print(f"{line}", end='\r', flush=True)
                
                time.sleep(0.1)
                idx += 1
        finally:
            print("\033[?25h", end="\r")
            if not inline_spinner:
                print(' ' * len(line), end='\r', flush=True)

    # --------------------------------------------------------------------------------- #

    def stop_animate(self):
        if self._animating:
            self._animating = False
            self._spinner_thread.join()
            self._spinner_thread = None

    # --------------------------------------------------------------------------------- #

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

#########################################################################################
# EOF                                                                                   #
#########################################################################################