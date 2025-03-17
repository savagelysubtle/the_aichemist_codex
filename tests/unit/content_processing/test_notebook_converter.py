import json
from pathlib import Path

import pytest

from the_aichemist_codex.backend.project_reader.notebooks import NotebookConverter


@pytest.mark.content_processing
@pytest.mark.unit

def test_notebook_conversion(tmp_path: Path) -> None:
    """Test extracting Python code from a Jupyter Notebook."""
    notebook_path = tmp_path / "test_notebook.ipynb"
    notebook_content = {
        "cells": [
            {"cell_type": "code", "source": ["print('Hello')\n"]},
            {"cell_type": "markdown", "source": ["# This is a heading"]},
        ]
    }
    notebook_path.write_text(json.dumps(notebook_content))

    script_output = NotebookConverter.to_script(notebook_path)

    assert "print('Hello')" in script_output  # noqa: S101
    assert "# This is a heading" not in script_output  # noqa: S101
