"""Unit tests for the analysis commands module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from the_aichemist_codex.interfaces.cli.cli import CLI
from the_aichemist_codex.interfaces.cli.commands import analysis


@pytest.fixture
def mock_console():
    """Create a mock rich console for testing output."""
    with patch("the_aichemist_codex.interfaces.cli.commands.analysis.console") as mock:
        yield mock


@pytest.fixture
def mock_summarize_code():
    """Mock the summarize_code function from the infrastructure layer."""
    with patch(
        "the_aichemist_codex.interfaces.cli.commands.analysis.summarize_code"
    ) as mock:
        # Return a sample analysis result
        mock.return_value = {
            "test_file.py": {
                "folder": "test_folder",
                "summary": "Test file summary",
                "functions": [
                    {
                        "name": "test_function",
                        "lineno": 10,
                        "args": ["arg1", "arg2"],
                        "docstring": "Test function docstring",
                    }
                ],
            }
        }
        yield mock


@pytest.fixture
def mock_process_file():
    """Mock the process_file function from the infrastructure layer."""
    with patch(
        "the_aichemist_codex.interfaces.cli.commands.analysis.process_file"
    ) as mock:
        # Return a sample file analysis result
        mock.return_value = (
            None,
            {
                "summary": "Test file summary",
                "functions": [
                    {
                        "name": "test_function",
                        "lineno": 10,
                        "args": ["arg1", "arg2"],
                        "docstring": "Test function docstring",
                    }
                ],
            },
        )
        yield mock


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing commands."""
    return CliRunner()


def test_register_commands():
    """Test registering analysis commands with the application."""
    app = MagicMock()
    cli = MagicMock()

    analysis.register_commands(app, cli)

    app.add_typer.assert_called_once()
    assert analysis._cli == cli


class TestScanCodebase:
    """Tests for the scan_codebase command."""

    def test_scan_nonexistent_directory(self, cli_runner, mock_console):
        """Test scanning a directory that doesn't exist."""
        # Setup mock CLI
        cli = CLI()
        analysis._cli = cli

        # Mock the handle_error method
        cli.handle_error = MagicMock()

        # Create a non-existent path
        non_existent_path = Path("non_existent_directory")

        # Call the function directly
        analysis.scan_codebase(str(non_existent_path))

        # Verify error handling
        cli.handle_error.assert_called_once()
        called_exception = cli.handle_error.call_args[0][0]
        assert isinstance(called_exception, FileNotFoundError)

    def test_scan_with_table_output(self, mock_summarize_code, mock_console):
        """Test scanning with table output format."""
        # Setup mock CLI
        cli = CLI()
        analysis._cli = cli

        # Create a temporary path
        temp_path = Path(".")

        # Call the function directly with default format (table)
        analysis.scan_codebase(str(temp_path))

        # Verify the summarize_code function was called
        mock_summarize_code.assert_called_once_with(temp_path.resolve())

        # Verify console output (at least that print was called)
        assert mock_console.print.call_count > 0

    def test_scan_with_json_output(self, mock_summarize_code, mock_console):
        """Test scanning with JSON output format."""
        # Setup mock CLI
        cli = CLI()
        analysis._cli = cli

        # Create a temporary path
        temp_path = Path(".")

        # Call the function with JSON format
        analysis.scan_codebase(str(temp_path), format="json")

        # Verify the summarize_code function was called
        mock_summarize_code.assert_called_once_with(temp_path.resolve())

        # Verify console output for JSON format
        mock_calls = mock_console.print.call_args_list
        assert any("Syntax" in str(call) for call in mock_calls)


class TestAnalyzeFile:
    """Tests for the analyze_file command."""

    def test_analyze_nonexistent_file(self, cli_runner, mock_console):
        """Test analyzing a file that doesn't exist."""
        # Setup mock CLI
        cli = CLI()
        analysis._cli = cli

        # Mock the handle_error method
        cli.handle_error = MagicMock()

        # Create a non-existent path
        non_existent_path = Path("non_existent_file.py")

        # Call the function directly
        analysis.analyze_file(str(non_existent_path))

        # Verify error handling
        cli.handle_error.assert_called_once()
        called_exception = cli.handle_error.call_args[0][0]
        assert isinstance(called_exception, FileNotFoundError)

    def test_analyze_non_python_file(self, cli_runner, mock_console):
        """Test analyzing a non-Python file."""
        # Setup mock CLI
        cli = CLI()
        analysis._cli = cli

        # Mock the handle_error method
        cli.handle_error = MagicMock()

        # Create a temporary text file
        with open("temp.txt", "w") as f:
            f.write("Test content")

        try:
            # Call the function directly
            analysis.analyze_file("temp.txt")

            # Verify error handling
            cli.handle_error.assert_called_once()
            called_exception = cli.handle_error.call_args[0][0]
            assert isinstance(called_exception, ValueError)
        finally:
            # Clean up
            Path("temp.txt").unlink(missing_ok=True)

    def test_analyze_file_with_docstrings(self, mock_process_file, mock_console):
        """Test analyzing a file with docstrings shown."""
        # Setup mock CLI
        cli = CLI()
        analysis._cli = cli

        # Create a temporary Python file
        with open("temp.py", "w") as f:
            f.write("def test(): pass")

        try:
            # Call the function directly
            analysis.analyze_file("temp.py", show_docstrings=True)

            # Verify process_file was called
            mock_process_file.assert_called_once()

            # Verify console output
            assert mock_console.print.call_count > 0
        finally:
            # Clean up
            Path("temp.py").unlink(missing_ok=True)
