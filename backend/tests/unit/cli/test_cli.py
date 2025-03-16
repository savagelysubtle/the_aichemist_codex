import sys
from argparse import ArgumentTypeError
from pathlib import Path

import pytest
from pytest import CaptureFixture, MonkeyPatch

from backend.cli import main, validate_directory


@pytest.mark.[a-z]+
@pytest.mark.[a-z]+

@pytest.mark.cli
@pytest.mark.unit
def test_validate_directory(tmp_path: Path) -> None:
    # Create a temporary directory and ensure it validates correctly.
    d = tmp_path / "test_dir"
    d.mkdir()
    result = validate_directory(str(d))
    assert result == d.resolve()  # noqa: S101


@pytest.mark.[a-z]+
@pytest.mark.[a-z]+

@pytest.mark.cli
@pytest.mark.unit
def test_validate_directory_failure(tmp_path: Path) -> None:
    # Ensure that a non-existent directory raises an argparse error.
    with pytest.raises(ArgumentTypeError):
        validate_directory(str(tmp_path / "nonexistent"))


@pytest.mark.[a-z]+
@pytest.mark.[a-z]+

@pytest.mark.cli
@pytest.mark.unit
def test_cli_read_command(
    tmp_path: Path, monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    # Create a temporary file with known content.
    test_file = tmp_path / "test.txt"
    test_file.write_text("This is a test file.")

    # Simulate CLI arguments for the "read" command.
    monkeypatch.setattr(
        sys, "argv", ["cli.py", "read", str(test_file), "--format", "auto"]
    )

    # Execute the CLI.
    main()

    # Capture stdout and verify that the file content is printed.
    captured = capsys.readouterr().out
    assert "This is a test file." in captured  # noqa: S101


@pytest.mark.[a-z]+
@pytest.mark.[a-z]+

@pytest.mark.cli
@pytest.mark.unit
def test_cli_tree_command(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    # Create a temporary directory with a file for tree generation.
    d = tmp_path / "test_tree"
    d.mkdir()
    (d / "file1.txt").write_text("File content", encoding="utf-8")

    # Use a temporary file as output for the file tree.
    output_file = tmp_path / "tree.json"

    # Simulate CLI arguments for the "tree" command.
    monkeypatch.setattr(
        sys, "argv", ["cli.py", "tree", str(d), "--output", str(output_file)]
    )

    # Execute the CLI.
    main()

    # Verify that the file tree output file is created.
    assert output_file.exists(), "File tree output file was not created."  # noqa: S101


# Additional tests for other commands can be added similarly.
