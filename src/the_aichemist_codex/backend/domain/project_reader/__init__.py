"""
Project reader module for analyzing and summarizing code.

This module provides functionality for reading, analyzing, and summarizing
code projects, extracting information about structure, functions, and other
code elements.
"""

from .models import InvalidVersion, Tag, Version
from .project_reader import ProjectReaderImpl

__all__ = ["ProjectReaderImpl", "Tag", "Version", "InvalidVersion"]
