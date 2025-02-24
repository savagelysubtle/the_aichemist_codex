import argparse
from pathlib import Path
from unittest.mock import patch

import project_reader.main as main_script


@patch("project_reader.main.Path.mkdir")
@patch("project_reader.main.Path.exists", return_value=False)
@patch("project_reader.main.logging.info")
def test_ensure_directory_exists(
    mock_logging_info, mock_path_exists, mock_mkdir, tmp_path
):
    """Test that ensure_directory_exists creates a directory when missing."""
    test_dir = tmp_path / "NewOutputDir"

    main_script.ensure_directory_exists(test_dir)

    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    # Normalize Windows paths for consistency
    actual_message = mock_logging_info.call_args[0][0].replace("\\", "/")
    expected_message = f"Creating output directory: {test_dir.as_posix()}"

    assert actual_message == expected_message


@patch(
    "src.project_reader.main.filedialog.askdirectory",
    return_value="C:/Users/TestProject",
)
def test_select_directory(mock_askdirectory):
    """Test if select_directory correctly uses Windows File Explorer."""
    result = main_script.select_directory("Select input directory")
    assert result == Path("C:/Users/TestProject")
    mock_askdirectory.assert_called_once()


@patch("project_reader.main.filedialog.askdirectory", return_value=None)
def test_select_directory_cancel(mock_askdirectory):
    """Test behavior when user cancels directory selection."""
    result = main_script.select_directory("Select directory")
    assert result is None
    mock_askdirectory.assert_called_once()


@patch.object(
    main_script, "select_directory", return_value=Path("C:/Users/TestProject")
)
@patch("argparse.ArgumentParser.parse_args")
def test_main_with_gui_selection(mock_parse_args, mock_select_directory, tmp_path):
    """Test default behavior where Windows File Explorer is used."""

    # ✅ Ensure `dir=None` so `select_directory()` gets called
    mock_parse_args.return_value = argparse.Namespace(dir=None, out=None)

    main_script.main(None, tmp_path)  # ✅ Explicitly pass `None`

    print(
        f"✅ mock_select_directory.call_count: {mock_select_directory.call_count}"
    )  # Debugging
    assert mock_select_directory.call_count > 0, "❌ select_directory() was not called!"

    mock_select_directory.assert_called()  # ✅ Now this should work
    mock_main.assert_called_with(Path("C:/Users/TestProject"), tmp_path)


@patch("argparse.ArgumentParser.parse_args")
def test_main_with_cli_args(mock_parse_args, tmp_path):
    """Test CLI arguments handling (no GUI selection)."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()

    mock_parse_args.return_value = argparse.Namespace(dir=input_dir, out=output_dir)

    with patch("project_reader.main.main") as mock_main:
        main_script.main(input_dir, output_dir)  # ✅ Directly call main()

    mock_main.assert_called_with(input_dir, output_dir)


@patch("project_reader.main.Path.exists", return_value=False)
@patch("project_reader.main.logging.error")
def test_main_invalid_directory(mock_logging_error, mock_path_exists):
    """Test error handling when input directory does not exist."""
    test_dir = Path("C:/InvalidDir")
    test_out = Path("C:/OutputDir")

    main_script.main(test_dir, test_out)

    mock_logging_error.assert_called_with("No valid directory selected for analysis.")
