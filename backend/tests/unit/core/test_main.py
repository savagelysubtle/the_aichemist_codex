# test_main.py
import tempfile
from pathlib import Path

import pytest

from backend.main import select_directory


# Fake implementations for GUI functions to bypass actual dialogs.
def fake_askdirectory(prompt: str) -> str:
    # Return a temporary directory path.
    return tempfile.gettempdir()


def fake_messagebox_info(title: str, message: str) -> None:
    return  # Simply bypass; in real tests you might capture/log the message.


@pytest.fixture(autouse=True)
def patch_tkinter(monkeypatch: pytest.MonkeyPatch) -> None:
    import tkinter.filedialog
    import tkinter.messagebox

    monkeypatch.setattr(tkinter.filedialog, "askdirectory", fake_askdirectory)
    monkeypatch.setattr(tkinter.messagebox, "showinfo", fake_messagebox_info)
    monkeypatch.setattr(tkinter.messagebox, "showerror", fake_messagebox_info)


@pytest.mark.core
@pytest.mark.unit
def test_select_directory() -> None:
    # Verify that select_directory returns a valid Path object.
    result = select_directory("Test prompt")
    assert isinstance(result, Path)  # noqa: S101
    assert result.exists()  # noqa: S101
