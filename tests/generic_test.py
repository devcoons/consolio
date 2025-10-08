import os
import sys
import time
import types
import builtins
from io import StringIO
import threading
import pytest

# Import the class under test. Adjust the import if your module/package name differs.
from consolio import Consolio, ConsolioUtils


class DummyStdout(StringIO):
    """A controllable stdout that pretends to be a TTY or not and exposes an encoding."""

    def __init__(self, *, isatty: bool, encoding: str = "utf-8"):
        super().__init__()
        self._isatty = isatty
        self._encoding = encoding

    def isatty(self):
        return self._isatty

    @property
    def encoding(self):
        return self._encoding


@pytest.fixture(autouse=True)
def _restore_env_and_streams(monkeypatch):
    # Ensure a clean environment for each test
    orig_stdout = sys.stdout
    env_backup = os.environ.copy()
    try:
        yield
    finally:
        sys.stdout = orig_stdout
        os.environ.clear()
        os.environ.update(env_backup)


# --------------------------------------------------------------------------------------
# Printing & wrapping
# --------------------------------------------------------------------------------------

def test_print_basic_status_and_indent(monkeypatch):
    dummy = DummyStdout(isatty=True)
    sys.stdout = dummy

    c = Consolio(no_colors=True, no_animation=True)
    c.print(1, "inf", "Hello world")

    out = dummy.getvalue()
    if out.startswith("\r"):
        out = out[1:]
    assert out.startswith("    [i] Hello world\n")

# --------------------------------------------------------------------------------------
# Color capability flags
# --------------------------------------------------------------------------------------

def test_no_color_env_disables_colors(monkeypatch):
    sys.stdout = DummyStdout(isatty=True)
    monkeypatch.setenv("NO_COLOR", "1")

    c = Consolio(no_colors=False, no_animation=True)
    c.print("inf", "plain text")
    out = sys.stdout.getvalue()
    assert "\x1b[" not in out 


def test_force_color_overrides(monkeypatch):
    # Even when not a TTY, FORCE_COLOR should enable color in our implementation
    sys.stdout = DummyStdout(isatty=False)
    monkeypatch.setenv("FORCE_COLOR", "1")

    c = Consolio(no_colors=False, no_animation=True)
    c.print("inf", "colored")
    out = sys.stdout.getvalue()
    assert "\x1b[" in out 


# --------------------------------------------------------------------------------------
# Animation capability flags
# --------------------------------------------------------------------------------------

def test_animation_disabled_in_ci(monkeypatch):
    sys.stdout = DummyStdout(isatty=True)
    monkeypatch.setenv("CI", "true")
    c = Consolio(no_animation=False)
    assert c.is_animation_supported() is False


# --------------------------------------------------------------------------------------
# Spinner context manager teardown
# --------------------------------------------------------------------------------------

def test_spinner_context_cleans_up(monkeypatch):
    # TTY so spinner can run
    sys.stdout = DummyStdout(isatty=True)
    c = Consolio(no_colors=True, no_animation=False)
    with c.spinner("Working", inline=False):
        time.sleep(0.2)
        assert c._animating is True
        assert isinstance(c._spinner_thread, threading.Thread)

    assert c._animating is False
    assert c._spinner_thread is None


# --------------------------------------------------------------------------------------
# Progress context manager
# --------------------------------------------------------------------------------------

def test_progress_context_updates_and_teardown(monkeypatch):
    sys.stdout = DummyStdout(isatty=True)
    c = Consolio(no_colors=True, no_animation=False)

    with c.progress(indent=1, initial_percentage=5) as update:
        time.sleep(0.1)
        update(55)
        time.sleep(0.1)
        assert c.current_progress == 55

    assert c._progressing is False
    assert c._progress_thread is None


# --------------------------------------------------------------------------------------
# Replace logic (TTY vs non-TTY)
# --------------------------------------------------------------------------------------

def test_replace_skips_when_not_tty(monkeypatch):
    sys.stdout = DummyStdout(isatty=False)
    c = Consolio(no_colors=True, no_animation=True)

    c.print("inf", "line 1")
    c.print("inf", "line 2", replace=True)
    out = sys.stdout.getvalue()

    assert "\033[F" not in out


def test_replace_uses_escapes_on_tty(monkeypatch):
    sys.stdout = DummyStdout(isatty=True)
    c = Consolio(no_colors=True, no_animation=True)

    c.print("inf", "first long line that will be replaced")
    sys.stdout.truncate(0); sys.stdout.seek(0)

    c.print("inf", "second", replace=True)
    out = sys.stdout.getvalue()
    assert "\033[F" in out 


# --------------------------------------------------------------------------------------
# Input handling
# --------------------------------------------------------------------------------------

def test_input_inline_and_hidden(monkeypatch):
    sys.stdout = DummyStdout(isatty=True)
    c = Consolio(no_colors=True, no_animation=True)

    monkeypatch.setattr(builtins, "input", lambda prompt="": "Alice")
    val = c.input(0, "Name?", inline=True, hidden=False)
    assert val == "Alice"

    monkeypatch.setattr("getpass.getpass", lambda prompt="": "s3cret")
    val2 = c.input(0, "Password?", inline=False, hidden=True)
    assert val2 == "s3cret"


# --------------------------------------------------------------------------------------
# Status validation
# --------------------------------------------------------------------------------------

def test_status_validation_raises():
    sys.stdout = DummyStdout(isatty=True)
    c = Consolio(no_colors=True, no_animation=True)

    with pytest.raises(ValueError):
        c.print("bogus", "text")
