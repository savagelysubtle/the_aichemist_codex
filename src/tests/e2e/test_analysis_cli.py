"""End-to-end tests for the AIchemist Codex analysis CLI commands."""

import os
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from the_aichemist_codex.interfaces.cli.cli import cli_app


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing commands."""
    return CliRunner()


@pytest.fixture
def sample_project():
    """Create a temporary project with Python files for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)

        # Create a simple project structure
        (project_dir / "src").mkdir()
        (project_dir / "tests").mkdir()

        # Create sample Python files
        with open(project_dir / "src" / "main.py", "w") as f:
            f.write("""
def add(a: int, b: int) -> int:
    \"\"\"Add two numbers and return the result.

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of a and b
    \"\"\"
    return a + b

def subtract(a: int, b: int) -> int:
    \"\"\"Subtract b from a and return the result.

    Args:
        a: First number
        b: Second number

    Returns:
        Difference between a and b
    \"\"\"
    return a - b
""")

        with open(project_dir / "src" / "utils.py", "w") as f:
            f.write("""
class Calculator:
    \"\"\"Simple calculator class.\"\"\"

    def __init__(self, initial: int = 0):
        \"\"\"Initialize the calculator with an initial value.

        Args:
            initial: Initial value
        \"\"\"
        self.value = initial

    def add(self, x: int) -> int:
        \"\"\"Add x to the current value.

        Args:
            x: Number to add

        Returns:
            New value
        \"\"\"
        self.value += x
        return self.value
""")

        with open(project_dir / "tests" / "test_main.py", "w") as f:
            f.write("""
import pytest
from src.main import add, subtract

def test_add():
    \"\"\"Test the add function.\"\"\"
    assert add(2, 3) == 5

def test_subtract():
    \"\"\"Test the subtract function.\"\"\"
    assert subtract(5, 3) == 2
""")

        yield project_dir


def test_analysis_scan_command(cli_runner, sample_project):
    """Test the 'aichemist analysis scan' command."""
    os.chdir(sample_project)

    # Run the scan command
    result = cli_runner.invoke(cli_app, ["analysis", "scan", "."])

    # Check the command executed successfully
    assert result.exit_code == 0

    # Check output contains expected information
    assert "Scanning codebase" in result.stdout
    assert "main.py" in result.stdout
    assert "utils.py" in result.stdout
    assert "test_main.py" in result.stdout


def test_analysis_scan_with_json_format(cli_runner, sample_project):
    """Test the 'aichemist analysis scan' command with JSON output format."""
    os.chdir(sample_project)

    # Run the scan command with JSON output
    result = cli_runner.invoke(cli_app, ["analysis", "scan", ".", "--format", "json"])

    # Check the command executed successfully
    assert result.exit_code == 0

    # Check JSON output markers
    assert "{" in result.stdout
    assert "}" in result.stdout


def test_analysis_file_command(cli_runner, sample_project):
    """Test the 'aichemist analysis file' command."""
    os.chdir(sample_project)

    # Run the file analysis command
    result = cli_runner.invoke(
        cli_app, ["analysis", "file", str(sample_project / "src" / "main.py")]
    )

    # Check the command executed successfully
    assert result.exit_code == 0

    # Check output contains expected information
    assert "Analyzing Python file" in result.stdout
    assert "add" in result.stdout
    assert "subtract" in result.stdout


def test_analysis_file_without_docstrings(cli_runner, sample_project):
    """Test the 'aichemist analysis file' command without docstrings."""
    os.chdir(sample_project)

    # Run the file analysis command without docstrings
    result = cli_runner.invoke(
        cli_app,
        [
            "analysis",
            "file",
            str(sample_project / "src" / "utils.py"),
            "--no-docstrings",
        ],
    )

    # Check the command executed successfully
    assert result.exit_code == 0

    # Check output contains expected information but not docstrings
    assert "Analyzing Python file" in result.stdout
    assert "Calculator" in result.stdout
    # Make sure the "Docstring" column header is not in the output
    assert "Docstring" not in result.stdout


def test_analysis_file_nonexistent(cli_runner, sample_project):
    """Test the 'aichemist analysis file' command with a nonexistent file."""
    os.chdir(sample_project)

    # Run the file analysis command with a nonexistent file
    result = cli_runner.invoke(cli_app, ["analysis", "file", "nonexistent.py"])

    # Check the command failed
    assert result.exit_code != 0

    # Check error message
    assert "Error" in result.stdout
    assert "File not found" in result.stdout


def test_analysis_complexity_command(cli_runner, sample_project):
    """Test the 'aichemist analysis complexity' command (stub)."""
    os.chdir(sample_project)

    # Run the complexity analysis command
    result = cli_runner.invoke(cli_app, ["analysis", "complexity", "."])

    # Check the command executed successfully
    assert result.exit_code == 0

    # Check output contains expected stub message
    assert "not yet implemented" in result.stdout


def test_analysis_dependencies_command(cli_runner, sample_project):
    """Test the 'aichemist analysis dependencies' command (stub)."""
    os.chdir(sample_project)

    # Run the dependencies analysis command
    result = cli_runner.invoke(cli_app, ["analysis", "dependencies", "."])

    # Check the command executed successfully
    assert result.exit_code == 0

    # Check output contains expected stub message
    assert "not yet implemented" in result.stdout
