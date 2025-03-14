# test_validator.py
import pytest
from backend.utils.validator import (
    get_project_name,
)  # For example, if this function validates a project name.


def test_get_project_name_success():
    name = get_project_name("MyProject")
    assert isinstance(name, str)
    assert name == "MyProject"


def test_get_project_name_failure():
    with pytest.raises(Exception):
        # Assuming invalid names raise an exception.
        get_project_name("")
