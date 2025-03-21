"""
Relationship detectors package.

This package contains various detector implementations for identifying
different types of relationships between files.
"""

from .directory_structure import DirectoryStructureDetector

__all__ = [
    "DirectoryStructureDetector",
]
