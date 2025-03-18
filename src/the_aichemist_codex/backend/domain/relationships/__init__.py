"""
Relationship Mapping Module.

This module provides functionality for detecting, storing, and querying
relationships between files. It enables visualization of file connections
and intelligent navigation between related content.
"""

from .detector import DetectionStrategy, RelationshipDetector
from .relationship import Relationship
from .relationship_manager import RelationshipManagerImpl

__all__ = [
    "Relationship",
    "DetectionStrategy",
    "RelationshipDetector",
    "RelationshipManagerImpl",
]
