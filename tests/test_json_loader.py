import json
from unittest.mock import mock_open, patch

from src.file_manager.json_loader import load_file_moves


def test_load_valid_json():
    """Test loading a valid JSON file."""
    mock_data = '{"file1.txt": "dest_folder", "file2.txt": "another_folder"}'

    with patch("builtins.open", mock_open(read_data=mock_data)):
        result = load_file_moves("fake.json")

    assert result == json.loads(mock_data)


def test_load_invalid_json():
    """Test handling of invalid JSON data."""
    with patch("builtins.open", mock_open(read_data="invalid json")):
        result = load_file_moves(
            "fake.json"
        )  # Expecting an empty dict, not an exception

    assert result == {}  # Function should return an empty dictionary on failure


def test_load_nonexistent_file():
    """Test handling of missing files."""
    with patch("builtins.open", side_effect=FileNotFoundError):
        result = load_file_moves("missing.json")

    assert result == {}  # Should return an empty dict on failure
