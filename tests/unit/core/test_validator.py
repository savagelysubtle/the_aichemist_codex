# test_validator.py
from pathlib import Path

import pytest

from the_aichemist_codex.backend.utils.validator import (
    get_project_name,
)  # For example, if this function validates a project name.


@pytest.mark.unit
@pytest.mark.unit

def test_get_project_name_success() -> None:
    name = get_project_name(Path("MyProject"))
    assert isinstance(name, str)  # noqa: S101
    assert name == "MyProject"  # noqa: S101


@pytest.mark.unit
@pytest.mark.unit

def test_get_project_name_failure() -> None:
    with pytest.raises(ValueError):
        # Assuming invalid names raise an exception.
        get_project_name(Path(""))
