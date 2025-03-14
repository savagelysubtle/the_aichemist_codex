# File: aichemist_codex/ingest/__init__.py
"""
Module: aichemist_codex/ingest/__init__.py

Description:
    This package acts as the orchestrator for the ingestion process in The Aichemist Codex.
    It coordinates standalone modules responsible for scanning directories, reading file content,
    and aggregating outputs into a comprehensive digest. The digest is designed to be fully ingestible
    by large language models for further processing.

Exports:
    - generate_digest(source_dir: Path, options: Optional[Dict[str, Any]] = None) -> str
      Generates a complete digest document for the given source directory.

Type Hints:
    - source_dir: Path — The root directory of the project to ingest.
    - options: Optional[Dict[str, Any]] — Configuration options (e.g., include/exclude patterns, file size limits).
    - Return: str — The aggregated digest output.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from .aggregator import aggregate_digest
from .reader import convert_notebook, read_full_file
from .scanner import scan_directory


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
