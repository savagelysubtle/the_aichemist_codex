"""
Tagging module for intelligent file organization.

This module provides functionality for managing file tags, including
automatic tag suggestion, hierarchical tag organization, and tag-based
file retrieval.
"""

from .hierarchy import TagHierarchy
from .manager import TagManager

__all__ = ["TagManager", "TagHierarchy"]
