"""Integration tests for the analysis commands with analysis infrastructure."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from the_aichemist_codex.infrastructure.analysis.code import (
    process_file,
    summarize_code,
)
from the_aichemist_codex.interfaces.cli.commands import analysis


@pytest.fixture
def sample_python_file():
    """Create a temporary Python file with sample content for testing."""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
        f.write("""
def test_function(arg1, arg2):
    \"\"\"
    Test function docstring.

    Args:
        arg1: First argument
        arg2: Second argument

    Returns:
        bool: Result of the test
    \"\"\"
    return True

class TestClass:
    \"\"\"Test class docstring.\"\"\"

    def __init__(self, name):
        \"\"\"Initialize the test class.\"\"\"
        self.name = name

    def test_method(self):
        \"\"\"Test method docstring.\"\"\"
        return self.name
""")
        temp_file = Path(f.name)

    try:
        yield temp_file
    finally:
        temp_file.unlink(missing_ok=True)


@pytest.fixture
def mock_cli():
    """Create a mock CLI instance."""

    class MockCLI:
        def __init__(self):
            self.errors = []

        def handle_error(self, error):
            self.errors.append(error)

    return MockCLI()


@pytest.mark.asyncio
async def test_scan_code_integration(sample_python_file, mock_cli):
    """Test that scan command correctly integrates with analysis infrastructure."""
    # Setup sample project directory
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)

        # Copy sample file to temp directory
        target_file = project_dir / "sample.py"
        with open(target_file, "w") as f:
            with open(sample_python_file) as src:
                f.write(src.read())

        # Set up the CLI reference
        analysis._cli = mock_cli

        # Run the summarize_code function directly
        result = await summarize_code(project_dir)

        # Check that the result contains our sample file
        assert str(target_file) in result

        # Check that the functions were correctly extracted
        file_data = result[str(target_file)]
        assert len(file_data["functions"]) == 3  # test_function, __init__, test_method

        # Check function details
        functions = file_data["functions"]
        function_names = [f["name"] for f in functions]
        assert "test_function" in function_names
        assert "__init__" in function_names
        assert "test_method" in function_names


@pytest.mark.asyncio
async def test_file_analysis_integration(sample_python_file, mock_cli):
    """Test that file analysis command correctly integrates with process_file."""
    # Set up the CLI reference
    analysis._cli = mock_cli

    # Process the file directly using the infrastructure function
    _, file_data = await process_file(sample_python_file)

    # Verify the summary and functions
    assert "summary" in file_data
    assert "functions" in file_data

    # Check extracted functions
    assert len(file_data["functions"]) == 3  # test_function, __init__, test_method

    # Check specific function details
    test_func = next(
        (f for f in file_data["functions"] if f["name"] == "test_function"), None
    )
    assert test_func is not None
    assert test_func["args"] == ["arg1", "arg2"]
    assert "Test function docstring" in test_func["docstring"]


@pytest.mark.parametrize("format_option", ["table", "json", "tree"])
def test_output_formats_integration(format_option, sample_python_file, mock_cli):
    """Test different output formats of the scan command work with real data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)

        # Copy sample file to temp directory
        target_file = project_dir / "sample.py"
        with open(target_file, "w") as f:
            with open(sample_python_file) as src:
                f.write(src.read())

        # Patch console.print to capture output
        with patch(
            "the_aichemist_codex.interfaces.cli.commands.analysis.console"
        ) as mock_console:
            # Set up the CLI reference
            analysis._cli = mock_cli

            # Run the scan command with the specified format
            analysis.scan_codebase(str(project_dir), format=format_option)

            # Verify console output
            assert mock_console.print.call_count > 0

            # Specific checks based on format
            if format_option == "json":
                # Check for Syntax in the mock calls for JSON output
                mock_calls = mock_console.print.call_args_list
                assert any("Syntax" in str(call) for call in mock_calls)
            elif format_option == "tree":
                # Check for Tree in the mock calls for tree output
                mock_calls = mock_console.print.call_args_list
                assert any("Tree" in str(call) for call in mock_calls)
            else:  # table format
                # Check for Table in the mock calls for table output
                mock_calls = mock_console.print.call_args_list
                assert any("Table" in str(call) for call in mock_calls)
