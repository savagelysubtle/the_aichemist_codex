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
      (Imported from .reader module)

Type Hints:
    - source_dir: Path — The root directory of the project to ingest.
    - options: Optional[Dict[str, Any]] — Configuration options (e.g., include/exclude patterns, file size limits).
    - Return: str — The aggregated digest output.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from .aggregator import aggregate_digest
from .reader import convert_notebook, generate_digest, read_full_file
from .scanner import scan_directory

# Re-export the generate_digest function from reader module
__all__ = ["generate_digest"]
