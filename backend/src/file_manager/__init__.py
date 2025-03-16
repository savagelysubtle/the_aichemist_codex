"""File management module for The Aichemist Codex."""

from .change_detector import ChangeDetector
from .change_history_manager import ChangeHistoryManager, change_history_manager
from .directory_manager import DirectoryManager
from .directory_monitor import DirectoryMonitor, directory_monitor
from .duplicate_detector import DuplicateDetector
from .file_mover import FileMover
from .file_tree import FileTreeGenerator
from .file_watcher import FileEventHandler, monitor_directory
from .sorter import RuleBasedSorter
from .version_manager import VersionManager, version_manager

__all__ = [
    "FileMover",
    "FileTreeGenerator",
    "monitor_directory",
    "DuplicateDetector",
    "FileEventHandler",
    "RuleBasedSorter",
    "DirectoryManager",
    "ChangeDetector",
    "ChangeHistoryManager",
    "change_history_manager",
    "DirectoryMonitor",
    "directory_monitor",
    "VersionManager",
    "version_manager",
]
