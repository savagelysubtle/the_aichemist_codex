# FILE: src/the_aichemist_codex/domain/relationships/__init__.py
"""Relationships domain module for AIchemist Codex.

This module defines the core concepts of relationships between entities.
"""

from .detector import DetectionStrategy, RelationshipDetectorBase
from .relationship import Relationship
from .relationship_type import RelationshipType

__all__ = [
    "DetectionStrategy",
    "Relationship",
    "RelationshipDetectorBase",
    "RelationshipType",
]
