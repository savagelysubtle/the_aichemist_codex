# test_main.py
import tempfile
from pathlib import Path

import pytest
from backend.main import select_directory


# Fake implementations for GUI functions to bypass actual dialogs.
def fake_askdirectory(prompt):
    # Return a temporary directory path.
    return tempfile.gettempdir()


def fake_messagebox_info(title, message):
    return  # Simply bypass; in real tests you might capture/log the message.


@pytest.fixture(autouse=True)
def patch_tkinter(monkeypatch):
    import tkinter.filedialog
    import tkinter.messagebox

    monkeypatch.setattr(tkinter.filedialog, "askdirectory", fake_askdirectory)
    monkeypatch.setattr(tkinter.messagebox, "showinfo", fake_messagebox_info)
    monkeypatch.setattr(tkinter.messagebox, "showerror", fake_messagebox_info)


def test_select_directory():
    # Verify that select_directory returns a valid Path object.
    result = select_directory("Test prompt")
    assert isinstance(result, Path)
    assert result.exists()
