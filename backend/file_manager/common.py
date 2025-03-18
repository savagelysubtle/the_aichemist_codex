"""
Common utilities and shared functionality for file management.

This module contains shared functionality between directory_monitor and file_watcher
to avoid circular dependencies.
"""

import logging
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class DirectoryPriority(Enum):
    """Priority levels for monitored directories."""

    CRITICAL = 0  # Highest priority, always process immediately
    HIGH = 1  # Process with minimal delay
    NORMAL = 2  # Standard processing
    LOW = 3  # Process when resources available


# Global set to track files being processed to avoid duplicate processing
files_being_processed: set[Path] = set()

# Global set to track directories being monitored
monitored_directories: set[Path] = set()


def is_file_being_processed(file_path: Path) -> bool:
    """Check if a file is currently being processed."""
    return file_path in files_being_processed


def mark_file_as_processing(file_path: Path) -> None:
    """Mark a file as being processed."""
    files_being_processed.add(file_path)


def mark_file_as_done_processing(file_path: Path) -> None:
    """Mark a file as done being processed."""
    if file_path in files_being_processed:
        files_being_processed.remove(file_path)


def is_directory_monitored(dir_path: Path) -> bool:
    """Check if a directory is being monitored."""
    return dir_path in monitored_directories


def add_monitored_directory(dir_path: Path) -> None:
    """Add a directory to the monitored set."""
    monitored_directories.add(dir_path)


def remove_monitored_directory(dir_path: Path) -> None:
    """Remove a directory from the monitored set."""
    if dir_path in monitored_directories:
        monitored_directories.remove(dir_path)


def get_throttle_for_priority(
    priority: DirectoryPriority, base_throttle: float
) -> float:
    """Get the throttle value for a given priority level."""
    if priority == DirectoryPriority.CRITICAL:
        return 0.0  # No throttling for critical directories
    elif priority == DirectoryPriority.HIGH:
        return base_throttle * 0.5  # Half throttling for high priority
    elif priority == DirectoryPriority.NORMAL:
        return base_throttle  # Normal throttling
    else:  # LOW priority
        return base_throttle * 2.0  # Double throttling for low priority
