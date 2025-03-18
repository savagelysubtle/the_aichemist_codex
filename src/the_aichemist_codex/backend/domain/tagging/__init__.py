"""
Tagging module for file organization.

This module provides functionality for managing file tags,
including creating, retrieving, updating, and deleting tags
and their associations with files.
"""

from .classifier import TagClassifier
from .hierarchy import TagHierarchy
from .suggester import TagSuggester
from .tagging_manager import TaggingManagerImpl

__all__ = ["TaggingManagerImpl", "TagHierarchy", "TagClassifier", "TagSuggester"]
