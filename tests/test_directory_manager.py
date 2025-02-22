import pytest
from pathlib import Path
from src.file_manager.directory_manager import DirectoryManager


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for testing."""
    return tmp_path / "test_directory"


def test_ensure_directory_creates_directory(temp_dir):
    """Ensure DirectoryManager creates a directory if it does not exist."""
    assert not temp_dir.exists()  # Confirm it doesn't exist initially
    DirectoryManager.ensure_directory(temp_dir)
    assert temp_dir.exists() and temp_dir.is_dir()  # Should now exist
