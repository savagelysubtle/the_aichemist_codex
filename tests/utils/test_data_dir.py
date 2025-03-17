"""Tests for data directory resolution logic."""

import os
import platform
from pathlib import Path
from unittest.mock import patch

import pytest

from the_aichemist_codex.backend.config.settings import (
    determine_project_root,
    initialize_directory_manager,
)


@pytest.fixture
def clean_environment():
    """Fixture to provide a clean environment for tests."""
    # Save original environment variables
    original_env = os.environ.copy()

    # Clear environment variables that might affect tests
    if "AICHEMIST_ROOT_DIR" in os.environ:
        del os.environ["AICHEMIST_ROOT_DIR"]
    if "AICHEMIST_DATA_DIR" in os.environ:
        del os.environ["AICHEMIST_DATA_DIR"]

    # Provide a clean environment for the test
    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


def get_test_path(path_str):
    """Convert a test path to a platform-appropriate format."""
    if platform.system() == "Windows":
        # On Windows, ensure we use the correct drive letter
        # and convert forward slashes to backslashes if needed
        if path_str.startswith("/"):
            path_str = f"D:{path_str}"
    return Path(path_str)


@patch("the_aichemist_codex.backend.config.settings.Path.exists")
def test_project_root_with_env_var(mock_exists, clean_environment):
    """Test project root detection with environment variable."""
    mock_exists.return_value = True
    test_path = "/test/root/dir"
    os.environ["AICHEMIST_ROOT_DIR"] = test_path

    result = determine_project_root()
    expected_path = get_test_path(test_path)
    assert result == expected_path


@patch("the_aichemist_codex.backend.config.settings.logger")
def test_data_dir_with_env_var(mock_logger, clean_environment):
    """Test data directory with environment variable."""
    test_path = "/test/data/dir"
    os.environ["AICHEMIST_DATA_DIR"] = test_path

    # Call the initialize_directory_manager function
    directory_manager = initialize_directory_manager()
    result = directory_manager.base_dir
    expected_path = get_test_path(test_path)
    assert result == expected_path


@patch("the_aichemist_codex.backend.config.settings.logger")
@patch(
    "the_aichemist_codex.backend.config.settings.PROJECT_ROOT", get_test_path("/test")
)
def test_data_dir_default(mock_logger, clean_environment):
    """Test data directory default case."""
    # Call the initialize_directory_manager function
    directory_manager = initialize_directory_manager()
    result = directory_manager.base_dir
    expected_path = get_test_path("/test/data")
    assert result == expected_path
