# File: aichemist_codex/ingest/aggregator.py
"""
Module: aichemist_codex/ingest/aggregator.py

Description:
    Aggregates the outputs from the scanning and reading stages into a single, well-formatted digest.
    This module compiles file metadata, full file contents, and directory structure into one document,
    formatted for optimal ingestion by language models. It also includes summary statistics such as file count,
    total size, and optionally token estimates.

Functions:
    - aggregate_digest(file_paths: List[Path], content_map: Dict[Path, str]) -> str
      Combines the list of file paths and their corresponding full content into a comprehensive digest string.

Type Hints:
    - file_paths: List[Path] — A list of file paths identified for ingestion.
    - content_map: Dict[Path, str] — A mapping of each file path to its complete text content.
    - Return: str — A formatted digest containing file headers, full content, and summary statistics.
"""

from pathlib import Path
from typing import Dict, List


def aggregate_digest(file_paths: List[Path], content_map: Dict[Path, str]) -> str:
    """
    Combines the list of file paths and their corresponding full content into a comprehensive digest string.

    Parameters:
        file_paths (List[Path]): A list of file paths identified for ingestion.
        content_map (Dict[Path, str]): A mapping of each file path to its complete text content.

    Returns:
        str: A formatted digest containing file headers, full content, and summary statistics.
    """
    lines = []
    total_files = len(file_paths)
    total_size = sum(fp.stat().st_size for fp in file_paths if fp.exists())

    lines.append("Project Digest Summary")
    lines.append(f"Total Files: {total_files}")
    lines.append(f"Total Size: {total_size} bytes")
    lines.append("")  # blank line

    for fp in file_paths:
        try:
            relative_path = fp.relative_to(fp.parents[1])
        except Exception:
            relative_path = fp
        lines.append(f"--- File: {relative_path} ---")
        lines.append(content_map.get(fp, ""))
        lines.append("")  # blank line between files

    return "\n".join(lines)
