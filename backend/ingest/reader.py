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
from typing import Any, Dict, Optional

from .aggregator import aggregate_digest
from .scanner import scan_directory


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


def generate_digest(source_dir: Path, options: Optional[Dict[str, Any]] = None) -> str:
    """
    Generates a complete digest document for the given source directory by coordinating scanning,
    file reading, and output aggregation.

    Parameters:
        source_dir (Path): The root directory of the project to ingest.
        options (Optional[Dict[str, Any]]): Configuration options such as include/exclude patterns and file size limits.

    Returns:
        str: The aggregated digest output.
    """
    # Get inclusion and exclusion patterns from options if provided.
    include_patterns = (
        options.get("include_patterns")
        if options and "include_patterns" in options
        else None
    )
    ignore_patterns = (
        options.get("ignore_patterns")
        if options and "ignore_patterns" in options
        else None
    )

    # Use the scanner to get a flat list of file paths.
    file_paths = scan_directory(source_dir, include_patterns, ignore_patterns)

    # Create a mapping from file paths to their full content.
    content_map = {}
    for file_path in file_paths:
        if file_path.suffix == ".ipynb":
            # For notebooks, convert the notebook using our dedicated function.
            include_output = (
                options.get("include_notebook_output", True) if options else True
            )
            content_map[file_path] = convert_notebook(
                file_path, include_output=include_output
            )
        else:
            # For other file types, read the full file content.
            content_map[file_path] = read_full_file(file_path)

    # Aggregate the results into a single digest string.
    digest = aggregate_digest(file_paths, content_map)
    return digest
