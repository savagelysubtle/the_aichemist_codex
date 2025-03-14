import json

from backend.project_reader.notebooks import NotebookConverter


def test_notebook_conversion(tmp_path):
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

    assert "print('Hello')" in script_output
    assert "# This is a heading" not in script_output
