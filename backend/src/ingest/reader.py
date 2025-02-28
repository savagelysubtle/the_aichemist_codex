# File: aichemist_codex/ingest/reader.py
"""
Module: aichemist_codex/ingest/reader.py

Description:
    Extends the functionality of the existing file_reader module to provide full-content extraction.
    This module defines functions for reading complete file content and for converting Jupyter notebooks
    into a consolidated text format. It supports multiple encodings and can optionally include cell outputs for notebooks.

Functions:
    - read_full_file(file_path: Path) -> str
      Reads and returns the entire content of a text file, handling multiple encodings as needed.

    - convert_notebook(notebook_path: Path, include_output: bool = True) -> str
      Converts a Jupyter notebook (.ipynb) into a continuous text format, with an option to include cell outputs.

Type Hints:
    - file_path / notebook_path: Path — The file to be processed.
    - include_output: bool — Flag to include cell outputs when processing notebooks (default True).
    - Return: str — The full text content of the file or the converted notebook.
"""

from pathlib import Path


def read_full_file(file_path: Path) -> str:
    """
    Reads and returns the entire content of a text file, handling multiple encodings as needed.

    Parameters:
        file_path (Path): The file to be processed.

    Returns:
        str: The full text content of the file.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(file_path, "r", encoding="latin-1") as f:
            return f.read()


def convert_notebook(notebook_path: Path, include_output: bool = True) -> str:
    """
    Converts a Jupyter notebook (.ipynb) into a continuous text format, with an option to include cell outputs.

    Parameters:
        notebook_path (Path): The notebook file to be processed.
        include_output (bool): Flag to include cell outputs (default True).

    Returns:
        str: The converted text content of the notebook.
    """
    import json

    try:
        with open(notebook_path, "r", encoding="utf-8") as f:
            nb = json.load(f)
    except Exception as e:
        return f"Error reading notebook: {e}"

    text = ""
    # Process each cell in the notebook.
    for cell in nb.get("cells", []):
        cell_type = cell.get("cell_type", "")
        source = "".join(cell.get("source", []))
        if cell_type == "code":
            text += "\n# Code:\n" + source
            if include_output:
                outputs = cell.get("outputs", [])
                if outputs:
                    text += "\n# Output:\n"
                    for output in outputs:
                        if "text" in output:
                            text += "".join(output["text"]) + "\n"
        elif cell_type in ["markdown", "raw"]:
            text += f"\n# {cell_type.capitalize()}:\n" + source + "\n"
    return text
