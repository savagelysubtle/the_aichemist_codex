import pytest
import shutil
from unittest.mock import patch
from project_generator.file_mover import FileMover


@pytest.fixture
def file_mover(tmp_path):
    """Fixture to initialize FileMover with a temp base directory."""
    return FileMover(base_dir=tmp_path)


@patch("shutil.move")
def test_move_file_success(mock_shutil_move, file_mover, tmp_path):
    """Test successful file move with a mock."""
    src = tmp_path / "test_file.txt"
    dest = "moved/test_file.txt"
    src.touch()  # Create a fake file

    assert file_mover.move_file(str(src), dest)  # Should return True
    mock_shutil_move.assert_called_once_with(str(src), str(tmp_path / dest))


@patch("shutil.move", side_effect=shutil.Error("Mocked error"))
def test_move_file_failure(mock_shutil_move, file_mover, tmp_path):
    """Test failure in moving a file."""
    src = tmp_path / "non_existent_file.txt"
    dest = "moved/non_existent_file.txt"

    assert not file_mover.move_file(str(src), dest)  # Should return False
