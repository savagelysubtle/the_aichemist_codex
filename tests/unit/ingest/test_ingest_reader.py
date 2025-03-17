from pathlib import Path

import pytest

# test_ingest_reader.py
from the_aichemist_codex.backend.ingest.reader import convert_notebook, read_full_file


@pytest.mark.ingest
@pytest.mark.ingest
@pytest.mark.ingest

def test_read_full_file(tmp_path: Path) -> None:
    # Create a sample text file.
    sample_file = tmp_path / "sample.txt"
    sample_text = "This is sample content for ingestion."
    sample_file.write_text(sample_text, encoding="utf-8")

    content = read_full_file(sample_file)
    assert sample_text in content  # noqa: S101


@pytest.mark.ingest
@pytest.mark.ingest
@pytest.mark.ingest

def test_read_full_file_fallback_encoding(tmp_path: Path) -> None:
    # Create a file encoded in latin-1.
    sample_file = tmp_path / "sample.txt"
    sample_text = "Café"  # Contains non-ASCII character.
    sample_file.write_text(sample_text, encoding="latin-1")

    content = read_full_file(sample_file)
    assert sample_text in content  # noqa: S101


@pytest.mark.ingest
@pytest.mark.ingest
@pytest.mark.ingest

def test_convert_notebook(tmp_path: Path) -> None:
    # Create a dummy notebook JSON file.
    notebook_file = tmp_path / "notebook.ipynb"
    notebook_content = {
        "cells": [
            {"cell_type": "code", "source": ["print('Hello')\n"], "outputs": []},
            {"cell_type": "markdown", "source": ["# Heading\n"]},
        ]
    }
    import json

    notebook_file.write_text(json.dumps(notebook_content), encoding="utf-8")

    converted = convert_notebook(notebook_file, include_output=True)
    assert "print('Hello')" in converted  # noqa: S101
    assert "# Heading" in converted  # noqa: S101
