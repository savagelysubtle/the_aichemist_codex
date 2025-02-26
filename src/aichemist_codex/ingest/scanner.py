# File: aichemist_codex/ingest/scanner.py
"""
Module: aichemist_codex/ingest/scanner.py

Description:
    Provides functionality for recursively scanning a directory to identify files that should be included
    in the ingestion process. This module applies user-defined inclusion and exclusion patterns, along with
    configurable limits, to produce a list of file paths.

Functions:
    - scan_directory(directory: Path,
                     include_patterns: Optional[Set[str]] = None,
                     ignore_patterns: Optional[Set[str]] = None) -> List[Path]
      Recursively scans the specified directory and returns a list of Path objects for files that meet the criteria.

Type Hints:
    - directory: Path — The directory to scan.
    - include_patterns: Optional[Set[str]] — Patterns for files to include.
    - ignore_patterns: Optional[Set[str]] — Patterns for files to exclude.
    - Return: List[Path] — A list of file paths that qualify for ingestion.
"""

from pathlib import Path
from typing import List, Optional, Set


def scan_directory(
    directory: Path,
    include_patterns: Optional[Set[str]] = None,
    ignore_patterns: Optional[Set[str]] = None,
) -> List[Path]:
    """
    Recursively scans the specified directory and returns a list of Path objects for files that meet the criteria.

    Parameters:
        directory (Path): The directory to scan.
        include_patterns (Optional[Set[str]]): Patterns for files to include.
        ignore_patterns (Optional[Set[str]]): Patterns for files to exclude.

    Returns:
        List[Path]: A list of file paths that qualify for ingestion.
    """
    files: List[Path] = []
    for item in directory.iterdir():
        if item.is_dir():
            files.extend(scan_directory(item, include_patterns, ignore_patterns))
        elif item.is_file():
            # Skip the file if it matches any ignore pattern.
            if ignore_patterns and any(
                item.match(pattern) for pattern in ignore_patterns
            ):
                continue
            # If include patterns are specified, only add the file if it matches one of them.
            if include_patterns and not any(
                item.match(pattern) for pattern in include_patterns
            ):
                continue
            files.append(item)
    return files
