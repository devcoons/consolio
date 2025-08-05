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
import platform
import getpass
import shutil
import time
import sys
import os
import signal

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
        effective_width = ((ConsolioUtils.get_terminal_size()[0] - 2) - indent) if sys.stdout.isatty() else 512
        lines = []
        while text:
            line = text[:effective_width]
            if len(text) > effective_width and ' ' in line:
                space_idx = line.rfind(' ')
                line = text[:space_idx]
                text = text[space_idx+1:]
            else:
                text = text[effective_width:]
            lines.append(line.strip())
        return lines

    # --------------------------------------------------------------------------------- #

    def detect_os():
        system = platform.system()
        if system == "Windows":
            return "windows"
        elif system == "Linux":
            return "linux"
        else:
            return system.lower()

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

    PROG_INF = [ '[i] ', FG_BL + '[i] ' + RESET ]
    PROG_WIP = [ '[-] ', FG_CB + '[-] ' + RESET ]
    PROG_WRN = [ '[!] ', FG_YW + '[!] ' + RESET ]
    PROG_ERR = [ '[x] ', FG_RD + '[x] ' + RESET ]
    PROG_CMP = [ '[v] ', FG_GR + '[v] ' + RESET ]
    PROG_QST = [ '[?] ', FG_BB + '[?] ' + RESET ]

    SPINNERS = {
        'dots':  ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷'],
        'braille': ['⠋', '⠙', '⠚', '⠞', '⠖', '⠦', '⠴', '⠲', '⠳', '⠓'],
        'default': ['|', '/', '-', '\\']
    }

    _last_message = []
    _last_indent = 0
    _last_text = ""
    _enabled_colors = True
    _status_prefixes = []
    _suspend = False
    _enabled_spinner = True
    _stop_event = threading.Event()

    # --------------------------------------------------------------------------------- #
    # --------------------------------------------------------------------------------- #

    def __init__(self, spinner_type='default', no_colors=False, no_animation=False):
        self._stop_event = threading.Event()
        self._animating = False
        self._progressing = False
        self._spinner_thread = None
        self._progress_thread = None
        self._suspend = False
        self._lock = threading.Lock()
        self._last_message = []
        self.spinner_type = spinner_type.lower()
        self.spinner_chars = self.SPINNERS.get(self.spinner_type, self.SPINNERS['default'])
        self.current_progress = 0

        self._enabled_colors = False if no_colors == True else self.is_color_supported()
        self._enabled_spinner = False if no_animation == True else self.is_animation_supported()

        if not self.is_spinner_supported(self.spinner_chars):
            self.spinner_type = 'default'
            self.spinner_chars = self.SPINNERS['default']

        self._status_prefixes = {
            "inf": self.PROG_INF[0 if self._enabled_colors == False else 1],
            "wip": self.PROG_WIP[0 if self._enabled_colors == False else 1],
            "wrn": self.PROG_WRN[0 if self._enabled_colors == False else 1],
            "err": self.PROG_ERR[0 if self._enabled_colors == False else 1],
            "cmp": self.PROG_CMP[0 if self._enabled_colors == False else 1]
        }

        self._last_status_prefix = ''
        self._last_indent = 0
        self._last_text = ''
        self._last_text_lines = []
        signal.signal(signal.SIGINT, self.cleanup_and_exit)   # Ctrl+C
        signal.signal(signal.SIGTERM, self.cleanup_and_exit)  # Termination

    # --------------------------------------------------------------------------------- #
    
    def cleanup_and_exit(self, signum, frame):
        try:
            self._stop_event.set()
            self.stop_animate()
        except Exception:
            pass
        sys.exit(1)
        
    # --------------------------------------------------------------------------------- #

    def start_progress(self, indent=0, initial_percentage=0):
        if self._suspend == True or self._enabled_spinner == False:
            return             
        with self._lock:
            self.stop_animate()
            self.stop_progress()
            self._progressing = True
            self.current_progress = initial_percentage
            self._progress_thread = threading.Thread(target=self._progress, args=(indent,), daemon=True)
            self._progress_thread.start()

    # --------------------------------------------------------------------------------- #

    def _progress(self, indent):
        if self._suspend == True or self._enabled_spinner == False:
            return            
        idx = 0
        spinner_position = 4 + (self._last_indent * 4)
        while self._progressing:
            if self._stop_event.is_set() or not threading.main_thread().is_alive():
                return
            spinner_char = self.spinner_chars[idx % len(self.spinner_chars)]
            indent_spaces = " " * (indent * 4)
            with self._lock:
                if self._enabled_colors == False:
                    line = f"{indent_spaces}[{spinner_char}] In progress: {self.current_progress}%"
                else:
                    line = f"{indent_spaces}{self.FG_BL}[{self.FG_MG}{spinner_char}{self.FG_BL}]{self.RESET} In progress: {self.FG_YW}{self.current_progress}%{self.RESET}"
                print(f"{line}", end='\r', flush=True)
            time.sleep(0.1)
            idx += 1
        with self._lock:
            print(' ' * shutil.get_terminal_size().columns, end='\r', flush=True)

    # --------------------------------------------------------------------------------- #

    def update_progress(self, percentage):
        if self._suspend == True or self._enabled_spinner == False:
            return          
        with self._lock:
            self.current_progress = percentage

    # --------------------------------------------------------------------------------- #

    def stop_progress(self):
        if self._suspend == True or self._enabled_spinner == False:
            return            
        if self._progressing:
            self._progressing = False
            self._progress_thread.join()
            self._progress_thread = None

    # --------------------------------------------------------------------------------- #
    
    def input(self, indent, question, inline=False, hidden=False, replace=False):
        if self._suspend == True:
            return
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

    def print(self, *args, replace=False):
        """
        Supports three signatures:
        - print(text, replace=False)
        - print(status, text, replace=False)
        - print(indent, status, text, replace=False)
        """
        if len(args) == 1:
            indent = self._last_indent
            status = "inf"
            text = args[0]
        elif len(args) == 2:
            indent = self._last_indent
            status, text = args
        elif len(args) == 3:
            indent, status, text = args
        else:
            raise TypeError("print() takes either 1, 2 or 3 positional arguments")

        if self._suspend:
            return

        self.stop_animate()
        self.stop_progress()

        status_prefix = self._status_prefixes.get(status, "")
        indent_spaces = " " * (indent * 4)

        with self._lock:
            if replace and sys.stdout.isatty():
                total_indent = (self._last_indent * 4) + 4
                text_lines = ConsolioUtils.split_text_to_fit(self._last_text, total_indent)[::-1]

                for ln in text_lines:
                    print(f"\033[F{' ' * (total_indent + len(ln))}", end='\r')

            self._last_status_prefix = status_prefix
            self._last_indent = indent
            self._last_text = text
            total_indent = len(indent_spaces) + 4
            total_indent_spaces = " " * total_indent
            text_lines = ConsolioUtils.split_text_to_fit(text, total_indent)

            rvar = '\r' if sys.stdout.isatty() else ''
            print(f"{rvar}{indent_spaces}{status_prefix}{text_lines[0]}")
            for ln in text_lines[1:]:
                print(f"{rvar}{total_indent_spaces}{ln}")

    # --------------------------------------------------------------------------------- #

    def start_animate(self, indent=0, inline_spinner=False):
        if self._suspend == True or self._enabled_spinner == False:
            return             
        self.stop_progress()       
        if self._animating:
            return
        self._stop_event = threading.Event()    
        self._animating = True
        self._spinner_thread = threading.Thread(target=self._animate, args=(indent, inline_spinner))
        self._spinner_thread.start()

    # --------------------------------------------------------------------------------- #

    def _animate(self, indent, inline_spinner):
        if self._suspend == True or self._enabled_spinner == False:
            return  
                  
        idx = 0
        with self._lock:
            print("\033[?25l", end="", flush=True)
        spinner_position = 4 + (self._last_indent * 4)
        
        try:
            while self._animating:
                spinner_char = self.spinner_chars[idx % len(self.spinner_chars)]
                if self._stop_event.is_set() or not threading.main_thread().is_alive():
                    return
                if inline_spinner:
                    with self._lock:
                        indent_spaces = " " * (self._last_indent * 4)
                        text_lines = ConsolioUtils.split_text_to_fit(self._last_text, len(indent_spaces) + 4)
                        if self._enabled_colors == False:
                            tline = f"{indent_spaces}[{spinner_char}] {text_lines[0]}"
                            line = ("\033[F" * len(text_lines)) + tline + ("\033[B" * len(text_lines))
                        else:
                            tline = f"{indent_spaces}{self.FG_BL}[{self.FG_MG}{spinner_char}{self.FG_BL}]{self.RESET} {text_lines[0]}"
                            line = ("\033[F" * len(text_lines)) + tline + ("\033[B" * len(text_lines))
                        print(line, end="", flush=True)
                else:
                    indent_spaces = " " * (indent * 4)
                    with self._lock:
                        if self._enabled_colors == False:
                            line = f"{indent_spaces} {spinner_char}"
                        else:
                            line = f"{indent_spaces} {self.FG_MG}{spinner_char}{self.RESET}"
                        print(f"{line}", end='\r', flush=True)
                
                time.sleep(0.1)
                idx += 1
        finally:
            print("\033[?25h", end="\r", flush=True)
            if not inline_spinner:
                print(' ' * len(line), end='\r', flush=True)

    # --------------------------------------------------------------------------------- #

    def stop_animate(self):
        if self._suspend == True or self._enabled_spinner == False:
            return         
        if self._animating:
            self._animating = False
            self._spinner_thread.join()
            self._spinner_thread = None

    # --------------------------------------------------------------------------------- #

    def is_spinner_supported(self, spinner_chars):
        if self._suspend == True or self._enabled_spinner == False:
            return False         
        encoding = sys.stdout.encoding or 'utf-8'
        for char in spinner_chars:
            try:
                char.encode(encoding)
            except UnicodeEncodeError:
                return False
            except Exception:
                return False
        return True

    # --------------------------------------------------------------------------------- #

    def is_animation_supported(self):
        try:
            if sys.stdout.isatty() == False:
                return False
            which_os = ConsolioUtils.detect_os()
            if which_os == 'windows':
                ver = platform.version()
                build = int(ver.split('.')[2])
                if build < 20000:
                    return False
                try:
                    '\r'.encode(sys.stdout.encoding)
                except:
                    return False
                return True
            elif which_os == 'linux':
                return False
            else:
                return False
        except:
            return False
    
    # --------------------------------------------------------------------------------- #

    def is_color_supported(self):
        try:
            if sys.stdout.isatty() == False:
                return False     
            
            which_os = ConsolioUtils.detect_os()

            if which_os == 'windows':
                try:
                    build = int(platform.version().split('.')[2])
                except:
                    build = 0

                is_windows_terminal = 'WT_SESSION' in os.environ
                is_vscode_terminal = 'TERM_PROGRAM' in os.environ and os.environ['TERM_PROGRAM'] == 'vscode'

                if build >= 20000 or is_windows_terminal or is_vscode_terminal:
                    return True
                
                if "ANSICON" in os.environ or "ConEmuANSI" in os.environ:
                    return True
                
                return False

            else:
                term = os.environ.get('TERM', '')
                if term in ('xterm', 'xterm-color', 'xterm-256color', 'screen', 'screen-256color', 'linux', 'vt100'):
                    return True
                
                if 'COLORTERM' in os.environ:
                    return True    
        except:
            return False

    # --------------------------------------------------------------------------------- #

    def _clear_previous_message(self):
        if self._suspend == True:
            return
        total_lines = len(self._last_text_lines)
        for _ in range(total_lines):
            print("\033[F\033[K", end='') 

    # --------------------------------------------------------------------------------- #
    
    def suspend(self):
        self.stop_progress()
        self._suspend = True

    # --------------------------------------------------------------------------------- #
    
    def resume(self):
        self._suspend = False

    # --------------------------------------------------------------------------------- #
    
    def plain(self):
        if self._animating:
            self._animating = False
            self._spinner_thread.join()
            self._spinner_thread = None    
        self._enabled_spinner = False 
        self._enabled_colors = False

    # --------------------------------------------------------------------------------- #
    
    def rich(self):
        self._enabled_spinner = self.is_animation_supported() 
        self._enabled_colors = self.is_color_supported()

    # --------------------------------------------------------------------------------- #
    
    def enable_animation(self):
        self._enabled_spinner = self.is_animation_supported()

    # --------------------------------------------------------------------------------- #
    
    def disable_animation(self):
        if self._animating:
            self._animating = False
            self._spinner_thread.join()
            self._spinner_thread = None    
        self._enabled_spinner = False  

#########################################################################################
# EOF                                                                                   #
#########################################################################################