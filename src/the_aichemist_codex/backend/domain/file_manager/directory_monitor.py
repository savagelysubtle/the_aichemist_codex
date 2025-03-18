"""
Directory monitor for watching file system changes.

This module provides functionality for monitoring directories for file changes
such as creation, modification, deletion, and movement.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    logger.warning("Watchdog library not available. Directory monitoring will be limited.")
    WATCHDOG_AVAILABLE = False
    Observer = object
    FileSystemEventHandler = object
    FileSystemEvent = object


class EventHandler(FileSystemEventHandler):
    """Custom event handler for file system events."""

    def __init__(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Initialize the event handler.

        Args:
            callback: Function to call when events are detected
        """
        self.callback = callback

    def on_any_event(self, event: FileSystemEvent) -> None:
        """
        Handle any file system event.

        Args:
            event: The file system event
        """
        # Skip directory events if configured to
        if event.is_directory:
            return

        # Convert the event to a dictionary
        event_data = {
            "type": event.event_type,
            "path": event.src_path,
            "is_directory": event.is_directory
        }

        # Add destination path for moved files
        if hasattr(event, 'dest_path'):
            event_data["dest_path"] = event.dest_path

        # Call the callback with event data
        if self.callback:
            self.callback(event_data)


class DirectoryMonitor:
    """
</rewritten_file>