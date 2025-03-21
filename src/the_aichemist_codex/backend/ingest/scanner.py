# File: aichemist_codex/ingest/scanner.py
"""
Module: aichemist_codex/ingest/scanner.py

Description:
    Provides functionality for recursively scanning a directory to identify files that should be included
    in the ingestion process. This module applies user-defined inclusion and exclusion patterns, along with
    configurable limits, to produce a list of file paths.

    It now leverages the default ignore patterns from SafeFileHandler as used in async_io.py.

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

from the_aichemist_codex.backend.utils.safety import SafeFileHandler


def scan_directory(
    directory: Path,
    include_patterns: set[str] | None = None,
    ignore_patterns: set[str] | None = None,
) -> list[Path]:
    """
    Recursively scans the specified directory and returns a list of Path objects for files that meet the criteria.

    Parameters:
        directory (Path): The directory to scan.
        include_patterns (Optional[Set[str]]): Patterns for files to include.
        ignore_patterns (Optional[Set[str]]): Patterns for files to exclude.

    Returns:
        List[Path]: A list of file paths that qualify for ingestion.
    """
    files: list[Path] = []
    for item in directory.iterdir():
        # Use the default ignore patterns via SafeFileHandler
        if SafeFileHandler.should_ignore(item):
            continue

        if item.is_dir():
            files.extend(scan_directory(item, include_patterns, ignore_patterns))
        elif item.is_file():
            # Additional ignore check using provided patterns
            if ignore_patterns and any(
                item.match(pattern) for pattern in ignore_patterns
            ):
                continue
            # Only include file if it matches one of the include patterns, if provided.
            if include_patterns and not any(
                item.match(pattern) for pattern in include_patterns
            ):
                continue
            files.append(item)
    return files
