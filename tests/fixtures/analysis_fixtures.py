"""Test fixtures for the analysis module."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def sample_code_snippet():
    """Return a sample Python code snippet for testing."""
    return """
def hello_world(name: str = "World") -> str:
    \"\"\"
    Return a greeting message.

    Args:
        name: The name to greet (default: "World")

    Returns:
        A greeting string
    \"\"\"
    return f"Hello, {name}!"

class Person:
    \"\"\"A simple person class.\"\"\"

    def __init__(self, name: str, age: int):
        \"\"\"
        Initialize a Person.

        Args:
            name: The person's name
            age: The person's age
        \"\"\"
        self.name = name
        self.age = age

    def greet(self) -> str:
        \"\"\"Return a greeting from this person.\"\"\"
        return f"Hi, I'm {self.name}!"

    def is_adult(self) -> bool:
        \"\"\"Check if the person is an adult (18+).\"\"\"
        return self.age >= 18
"""


@pytest.fixture
def sample_python_project():
    """Create a sample Python project structure for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)

        # Create project structure
        src_dir = project_dir / "src" / "myproject"
        src_dir.mkdir(parents=True)
        tests_dir = project_dir / "tests"
        tests_dir.mkdir()

        # Create __init__.py files
        (src_dir / "__init__.py").touch()
        (tests_dir / "__init__.py").touch()

        # Create some Python files
        with open(src_dir / "core.py", "w") as f:
            f.write("""
\"\"\"Core module for the sample project.\"\"\"

def calculate_sum(numbers: list[int]) -> int:
    \"\"\"
    Calculate the sum of a list of numbers.

    Args:
        numbers: A list of integers

    Returns:
        Sum of all numbers
    \"\"\"
    return sum(numbers)

def calculate_average(numbers: list[int]) -> float:
    \"\"\"
    Calculate the average of a list of numbers.

    Args:
        numbers: A list of integers

    Returns:
        Average of the numbers
    \"\"\"
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)
""")

        with open(src_dir / "utils.py", "w") as f:
            f.write("""
\"\"\"Utility functions for the sample project.\"\"\"

from typing import Any

def is_empty(value: Any) -> bool:
    \"\"\"
    Check if a value is empty.

    Args:
        value: Any value

    Returns:
        True if the value is considered empty, False otherwise
    \"\"\"
    if value is None:
        return True
    if isinstance(value, (str, list, dict, set, tuple)):
        return len(value) == 0
    return False

def get_or_default(data: dict, key: str, default: Any = None) -> Any:
    \"\"\"
    Safely get a value from a dictionary with a default fallback.

    Args:
        data: The dictionary to get the value from
        key: The key to look up
        default: The default value to return if the key is not found

    Returns:
        The value from the dictionary or the default
    \"\"\"
    return data.get(key, default)
""")

        with open(tests_dir / "test_core.py", "w") as f:
            f.write("""
\"\"\"Tests for the core module.\"\"\"

import pytest
from src.myproject.core import calculate_sum, calculate_average

def test_calculate_sum():
    \"\"\"Test the calculate_sum function.\"\"\"
    assert calculate_sum([1, 2, 3]) == 6
    assert calculate_sum([]) == 0

def test_calculate_average():
    \"\"\"Test the calculate_average function.\"\"\"
    assert calculate_average([2, 4, 6]) == 4.0
    assert calculate_average([]) == 0.0
""")

        # Add a requirements.txt file
        with open(project_dir / "requirements.txt", "w") as f:
            f.write("""
pytest>=7.0.0
rich>=10.0.0
typing-extensions>=4.0.0
""")

        # Add a README.md file
        with open(project_dir / "README.md", "w") as f:
            f.write("""
# Sample Project

This is a sample Python project for testing the AIchemist Codex analysis module.

## Features

- Core calculation functions
- Utility helpers
- Comprehensive test suite
""")

        yield project_dir


@pytest.fixture
def expected_code_analysis_result():
    """Return expected result structure for code analysis."""
    return {
        "some_file.py": {
            "folder": "some_folder",
            "summary": "This is a Python module with functions and classes.",
            "functions": [
                {
                    "name": "hello_world",
                    "lineno": 2,
                    "args": ["name"],
                    "docstring": "Return a greeting message.",
                },
                {
                    "name": "__init__",
                    "lineno": 14,
                    "args": ["self", "name", "age"],
                    "docstring": "Initialize a Person.",
                },
                {
                    "name": "greet",
                    "lineno": 25,
                    "args": ["self"],
                    "docstring": "Return a greeting from this person.",
                },
                {
                    "name": "is_adult",
                    "lineno": 29,
                    "args": ["self"],
                    "docstring": "Check if the person is an adult (18+).",
                },
            ],
        }
    }
