"""Core module for The AIChemist Codex.

This package contains core interfaces, models, and exceptions.
"""

# Re-export core model classes
from .models import (
    DirectoryInfo,
    FileInfo,
    FileMetadata,
    Relationship,
    SearchResult,
)

# Define exported symbols
__all__ = [
    "DirectoryInfo",
    "FileInfo",
    "FileMetadata",
    "Relationship",
    "SearchResult",
]
