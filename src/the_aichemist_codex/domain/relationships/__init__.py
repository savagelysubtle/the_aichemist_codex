"""Relationships domain module for AIchemist Codex.

This module provides functionality for managing and tracking relationships between files
in a codebase, including creating, finding, and analyzing file relationships.
"""

from .manager import RelationshipManager
from .relationship import Relationship
from .relationship_type import RelationshipType

__all__ = ["RelationshipManager", "Relationship", "RelationshipType"]
