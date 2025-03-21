"""
Relationship Mapping Module.

This module provides functionality for detecting, storing, and querying
relationships between files. It enables visualization of file connections
and intelligent navigation between related content.
"""

from .detector import DetectionStrategy, RelationshipDetector
from .graph import RelationshipGraph
from .relationship import Relationship, RelationshipType
from .store import RelationshipStore

__all__ = [
    "Relationship",
    "RelationshipType",
    "RelationshipDetector",
    "DetectionStrategy",
    "RelationshipStore",
    "RelationshipGraph",
]
