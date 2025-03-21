"""
Directory monitor for watching file system changes.

This module provides functionality for monitoring directories for file changes
such as creation, modification, deletion, and movement. It follows the adapter
pattern to abstract the dependency on the watchdog library.
"""

import asyncio
import logging
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol, Union

logger = logging.getLogger(__name__)

# Type aliases for better readability
PathLike = Union[str, Path]
EventCallback = Callable[[dict[str, Any]], None]
EventData = dict[str, Any]


# Protocols (these are only used at type checking time)
class FileSystemEventProtocol(Protocol):
    """Protocol for file system events."""

    event_type: str
    src_path: str
    is_directory: bool


class FileSystemMonitorAdapter:
    """
    Base adapter class for file system monitoring.

    This class provides an abstraction layer for file system monitoring,
    allowing different implementations to be used depending on availability
    of libraries.
    """

    @staticmethod
    def create_monitor(directory: Path, callback: EventCallback) -> "DirectoryMonitor":
        """
        Factory method to create a directory monitor with the appropriate adapter.

        Args:
            directory: Directory to monitor
            callback: Function to call when events are detected

        Returns:
            A directory monitor configured with the appropriate adapter
        """
        monitor = DirectoryMonitor(directory, callback)
        return monitor


# Flag to track watchdog availability
WATCHDOG_AVAILABLE = False

# Try to import watchdog and define adapter if available
try:
    from watchdog.events import FileSystemEvent, FileSystemEventHandler
    from watchdog.observers import Observer

    # Indicate that watchdog is available
    WATCHDOG_AVAILABLE = True

    class WatchdogAdapter(FileSystemEventHandler):
        """Adapter for watchdog events."""

        def __init__(self, callback: EventCallback) -> None:
            """
            Initialize the adapter.

            Args:
                callback: Function to call when events are detected
            """
            super().__init__()
            self.callback = callback

        def on_any_event(self, event: Any) -> None:
            """
            Handle any file system event from watchdog.

            Args:
                event: Watchdog event
            """
            # Skip directory events
            if hasattr(event, "is_directory") and event.is_directory:
                return

            # Convert to common event data format
            event_data: EventData = {
                "type": getattr(event, "event_type", "unknown"),
                "path": getattr(event, "src_path", ""),
                "is_directory": getattr(event, "is_directory", False),
            }

            # Add destination path for move events
            if hasattr(event, "dest_path"):
                event_data["dest_path"] = event.dest_path

            # Call the callback with event data
            if self.callback:
                self.callback(event_data)

    class WatchdogEventSource:
        """Event source using watchdog."""

        def __init__(self) -> None:
            """Initialize the event source."""
            self.observer = Observer()
            self.handlers: dict[str, WatchdogAdapter] = {}

        def register(
            self, path: PathLike, handler: WatchdogAdapter, recursive: bool = False
        ) -> None:
            """
            Register a handler for events on a path.

            Args:
                path: Path to monitor
                handler: Event handler
                recursive: Whether to monitor subdirectories
            """
            path_str = str(path)
            self.handlers[path_str] = handler
            self.observer.schedule(handler, path_str, recursive=recursive)

        def start(self) -> None:
            """Start monitoring."""
            self.observer.start()

        def stop(self) -> None:
            """Stop monitoring."""
            self.observer.stop()
            self.observer.join()

        def is_available(self) -> bool:
            """Check if this implementation is available."""
            return True

    # Create watchdog-based monitoring components
    def create_handler(callback: EventCallback) -> Any:
        """Create watchdog event handler."""
        return WatchdogAdapter(callback)

    def create_event_source() -> Any:
        """Create watchdog event source."""
        return WatchdogEventSource()

except ImportError:
    # Watchdog not available, create dummy implementations
    logger.warning(
        "Watchdog library not available. Directory monitoring will be limited."
    )

    class FallbackAdapter:
        """Fallback adapter when watchdog is not available."""

        def __init__(self, callback: EventCallback) -> None:
            """
            Initialize the adapter.

            Args:
                callback: Function to call when events are detected
            """
            self.callback = callback

        def on_any_event(self, event: Any) -> None:
            """
            Handle any file system event (non-functional in fallback mode).

            Args:
                event: Event data
            """
            logger.warning("Event handling not available without watchdog")

    class FallbackEventSource:
        """Fallback event source when watchdog is not available."""

        def __init__(self) -> None:
            """Initialize the event source."""
            self.running = False
            self.handlers: dict[str, FallbackAdapter] = {}

        def register(
            self, path: PathLike, handler: FallbackAdapter, recursive: bool = False
        ) -> None:
            """
            Register a handler for events on a path (non-functional in fallback mode).

            Args:
                path: Path to monitor
                handler: Event handler
                recursive: Whether to monitor subdirectories
            """
            path_str = str(path)
            self.handlers[path_str] = handler
            logger.warning(f"Cannot monitor {path_str} - watchdog not available")

        def start(self) -> None:
            """Start monitoring (non-functional in fallback mode)."""
            self.running = True
            logger.warning(
                "Monitor started in limited mode (no file events will be detected)"
            )

        def stop(self) -> None:
            """Stop monitoring (non-functional in fallback mode)."""
            self.running = False
            logger.warning("Monitor stopped")

        def is_available(self) -> bool:
            """Check if this implementation is available."""
            return False

    # Create fallback monitoring components
    def create_handler(callback: EventCallback) -> Any:
        """Create fallback event handler."""
        return FallbackAdapter(callback)

    def create_event_source() -> Any:
        """Create fallback event source."""
        return FallbackEventSource()


class DirectoryMonitor:
    """
    Directory monitoring service.

    This class provides functionality for watching directory changes and
    triggering callbacks when files are created, modified, or deleted.
    It uses the adapter pattern to abstract the dependency on specific
    monitoring libraries.
    """

    def __init__(self, directory: Path, callback: EventCallback) -> None:
        """
        Initialize the directory monitor.

        Args:
            directory: The directory to monitor
            callback: Function to call when events are detected
        """
        self.directory = directory
        self.callback = callback
        self.handler = create_handler(callback)
        self.event_source = create_event_source()

    async def start(self) -> None:
        """Start monitoring the directory."""
        self.event_source.register(self.directory, self.handler, recursive=True)
        self.event_source.start()

    async def stop(self) -> None:
        """Stop monitoring the directory."""
        self.event_source.stop()

    async def monitor(self) -> None:
        """Monitor the directory for changes."""
        try:
            await self.start()
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await self.stop()
        except Exception as e:
            logger.error(f"Error monitoring directory: {e}")
            await self.stop()

    async def monitor_file(self, file_path: Path) -> None:
        """
        Monitor a specific file for changes.

        Args:
            file_path: Path to the file to monitor
        """
        try:
            # Create a temporary event source to monitor the file
            temp_handler = create_handler(self.callback)
            temp_source = create_event_source()
            temp_source.register(file_path.parent, temp_handler, recursive=False)
            temp_source.start()

            # Wait for the file to be modified
            await asyncio.sleep(1)

            # Stop monitoring the file
            temp_source.stop()
        except Exception as e:
            logger.error(f"Error monitoring file: {e}")

    async def monitor_directory(self, directory: Path) -> None:
        """
        Monitor a specific directory for changes.

        Args:
            directory: Path to the directory to monitor
        """
        try:
            # Create a temporary event source to monitor the directory
            temp_handler = create_handler(self.callback)
            temp_source = create_event_source()
            temp_source.register(directory, temp_handler, recursive=True)
            temp_source.start()

            # Wait for changes
            await asyncio.sleep(1)

            # Stop monitoring
            temp_source.stop()
        except Exception as e:
            logger.error(f"Error monitoring directory: {e}")

    async def monitor_file_or_directory(self, path: Path) -> None:
        """
        Monitor a file or directory for changes.

        Args:
            path: Path to monitor
        """
        try:
            if path.is_file():
                await self.monitor_file(path)
            elif path.is_dir():
                await self.monitor_directory(path)
            else:
                logger.error(f"Invalid path: {path}")
        except Exception as e:
            logger.error(f"Error monitoring path: {e}")

    async def monitor_all(self) -> None:
        """Monitor all files and directories in the monitored directory."""
        try:
            for root, _, files in os.walk(self.directory):
                for file in files:
                    file_path = Path(root) / file
                    await self.monitor_file_or_directory(file_path)
        except Exception as e:
            logger.error(f"Error monitoring all files and directories: {e}")

    async def monitor_all_recursive(self) -> None:
        """Monitor all files and directories recursively."""
        try:

            async def monitor_recursive(path: Path) -> None:
                await self.monitor_file_or_directory(path)
                if path.is_dir():
                    for subdir in path.iterdir():
                        await monitor_recursive(subdir)

            await monitor_recursive(self.directory)
        except Exception as e:
            logger.error(f"Error monitoring recursively: {e}")

    async def monitor_all_recursive_with_depth(self, max_depth: int) -> None:
        """
        Monitor recursively up to a specified depth.

        Args:
            max_depth: Maximum depth to monitor
        """
        try:

            async def monitor_recursive(path: Path, depth: int) -> None:
                await self.monitor_file_or_directory(path)
                if path.is_dir() and depth < max_depth:
                    for subdir in path.iterdir():
                        await monitor_recursive(subdir, depth + 1)

            await monitor_recursive(self.directory, 0)
        except Exception as e:
            logger.error(f"Error monitoring with depth: {e}")
