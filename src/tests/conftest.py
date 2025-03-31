"""Pytest configuration file for the AIchemist Codex tests."""

import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

# Import fixtures that should be available to all tests


@pytest.fixture
def temp_dir() -> Iterator[Path]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_path:
        path = Path(temp_path)
        yield path


@pytest.fixture
def backup_cwd() -> Iterator[None]:
    """
    Save and restore the current working directory.

    This is useful for tests that change the working directory.
    """
    old_cwd = os.getcwd()
    try:
        yield
    finally:
        os.chdir(old_cwd)


@pytest.fixture
def temp_workspace(temp_dir: Path, backup_cwd: None) -> Path:
    """
    Create a temporary workspace with proper test isolation.

    This fixture:
    1. Creates a temporary directory
    2. Changes the working directory to that directory
    3. Yields the path for test use
    4. Changes back to the original directory after the test

    Returns:
        Path to the temporary workspace
    """
    os.chdir(temp_dir)
    return temp_dir


@pytest.fixture
def create_test_file():
    """
    Fixture to create a test file with given content.

    Returns:
        Function to create a test file with specified path and content
    """

    def _create_file(file_path: str | Path, content: str) -> Path:
        """
        Create a test file with the given content.

        Args:
            file_path: Path to the file to create
            content: Content to write to the file

        Returns:
            Path to the created file
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            f.write(content)

        return path

    return _create_file
