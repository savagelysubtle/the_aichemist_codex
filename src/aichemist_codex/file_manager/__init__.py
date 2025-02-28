"""File management module for The Aichemist Codex."""

from .directory_manager import DirectoryManager
from .duplicate_detector import DuplicateDetector
from .file_mover import FileMover
from .file_tree import FileTreeGenerator
from .file_watcher import FileEventHandler, monitor_directory
from .sorter import RuleBasedSorter

__all__ = [
    "FileMover",
    "FileTreeGenerator",
    "monitor_directory",
    "DuplicateDetector",
    "FileEventHandler",
    "RuleBasedSorter",
    "DirectoryManager",
]
