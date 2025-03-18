"""
File management module for The Aichemist Codex.

This module provides functionality for file operations such as moving, copying,
detecting changes, versioning, and monitoring directories for changes.
"""

from .file_manager import FileManagerImpl
from .change_detector import ChangeDetector
from .directory_monitor import DirectoryMonitor

__all__ = [
    "FileManagerImpl",
    "ChangeDetector",
    "DirectoryMonitor"
]
