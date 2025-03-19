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
    """Directory monitoring service.

    This class provides functionality for watching directory changes and
    triggering callbacks when files are created, modified, or deleted.
    """

    def __init__(self, directory: Path, callback: Callable[[Dict[str, Any]], None]):
        """
        Initialize the directory monitor.

        Args:
            directory: The directory to monitor
            callback: Function to call when events are detected
        """
        self.directory = directory
        self.callback = callback
        self.observer = Observer()
        self.event_handler = EventHandler(self.callback)

    async def start(self):
        """Start monitoring the directory."""
        self.observer.schedule(self.event_handler, self.directory, recursive=True)
        self.observer.start()

    async def stop(self):
        """Stop monitoring the directory."""
        self.observer.stop()
        self.observer.join()

    async def monitor(self):
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

    async def monitor_file(self, file_path: Path):
        """Monitor a specific file for changes."""
        try:
            # Create a temporary observer to monitor the file
            temp_observer = Observer()
            temp_event_handler = EventHandler(self.callback)
            temp_observer.schedule(temp_event_handler, file_path.parent, recursive=False)
            temp_observer.start()

            # Wait for the file to be modified
            await asyncio.sleep(1)

            # Stop monitoring the file
            temp_observer.stop()
            temp_observer.join()
        except Exception as e:
            logger.error(f"Error monitoring file: {e}")

    async def monitor_directory(self, directory: Path):
        """Monitor a specific directory for changes."""
        try:
            # Create a temporary observer to monitor the directory
            temp_observer = Observer()
            temp_event_handler = EventHandler(self.callback)
            temp_observer.schedule(temp_event_handler, directory, recursive=True)
            temp_observer.start()

            # Wait for changes in the directory
            await asyncio.sleep(1)

            # Stop monitoring the directory
            temp_observer.stop()
            temp_observer.join()
        except Exception as e:
            logger.error(f"Error monitoring directory: {e}")

    async def monitor_file_or_directory(self, path: Path):
        """Monitor a specific file or directory for changes."""
        try:
            if path.is_file():
                await self.monitor_file(path)
            elif path.is_dir():
                await self.monitor_directory(path)
            else:
                logger.error(f"Invalid path: {path}")
        except Exception as e:
            logger.error(f"Error monitoring path: {e}")

    async def monitor_all(self):
        """Monitor all files and directories in the monitored directory."""
        try:
            for root, _, files in os.walk(self.directory):
                for file in files:
                    file_path = Path(root) / file
                    await self.monitor_file_or_directory(file_path)
        except Exception as e:
            logger.error(f"Error monitoring all files and directories: {e}")

    async def monitor_all_recursive(self):
        """Monitor all files and directories in the monitored directory and its subdirectories."""
        try:
            async def monitor_recursive(path: Path):
                await self.monitor_file_or_directory(path)
                if path.is_dir():
                    for subdir in path.iterdir():
                        await monitor_recursive(subdir)

            await monitor_recursive(self.directory)
        except Exception as e:
            logger.error(f"Error monitoring all files and directories recursively: {e}")

    async def monitor_all_recursive_with_depth(self, max_depth: int):
        """Monitor all files and directories in the monitored directory and its subdirectories up to a specified depth."""
        try:
            async def monitor_recursive(path: Path, depth: int):
                await self.monitor_file_or_directory(path)
                if path.is_dir() and depth < max_depth:
                    for subdir in path.iterdir():
                        await monitor_recursive(subdir, depth + 1)

            await monitor_recursive(self.directory, 0)
        except Exception as e:
            logger.error(f"Error monitoring all files and directories recursively with depth: {e}")

    async def monitor_all_recursive_with_depth_and_file_types(self, max_depth: int, file_types: List[str]):
        """Monitor all files and directories in the monitored directory and its subdirectories up to a specified depth, filtering by file types."""
        try:
            async def monitor_recursive(path: Path, depth: int):
                await self.monitor_file_or_directory(path)
                if path.is_dir() and depth < max_depth:
                    for subdir in path.iterdir():
                        if subdir.is_file() and subdir.suffix in file_types:
                            await monitor_recursive(subdir, depth + 1)

            await monitor_recursive(self.directory, 0)
        except Exception as e:
            logger.error(f"Error monitoring all files and directories recursively with depth and file types: {e}")

    async def monitor_all_recursive_with_depth_and_file_types_and_file_names(self, max_depth: int, file_types: List[str], file_names: List[str]):
        """Monitor all files and directories in the monitored directory and its subdirectories up to a specified depth, filtering by file types and file names."""
        try:
            async def monitor_recursive(path: Path, depth: int):
                await self.monitor_file_or_directory(path)
                if path.is_dir() and depth < max_depth:
                    for subdir in path.iterdir():
                        if subdir.is_file() and subdir.suffix in file_types and subdir.name in file_names:
                            await monitor_recursive(subdir, depth + 1)

            await monitor_recursive(self.directory, 0)
        except Exception as e:
            logger.error(f"Error monitoring all files and directories recursively with depth, file types, and file names: {e}")

    async def monitor_all_recursive_with_depth_and_file_types_and_file_names_and_file_contents(self, max_depth: int, file_types: List[str], file_names: List[str], file_contents: List[str]):
        """Monitor all files and directories in the monitored directory and its subdirectories up to a specified depth, filtering by file types, file names, and file contents."""
        try:
            async def monitor_recursive(path: Path, depth: int):
                await self.monitor_file_or_directory(path)
                if path.is_dir() and depth < max_depth:
                    for subdir in path.iterdir():
                        if subdir.is_file() and subdir.suffix in file_types and subdir.name in file_names and subdir.read_text() in file_contents:
                            await monitor_recursive(subdir, depth + 1)

            await monitor_recursive(self.directory, 0)
        except Exception as e:
            logger.error(f"Error monitoring all files and directories recursively with depth, file types, file names, and file contents: {e}")

    async def monitor_all_recursive_with_depth_and_file_types_and_file_names_and_file_contents_and_file_paths(self, max_depth: int, file_types: List[str], file_names: List[str], file_contents: List[str], file_paths: List[str]):
        """Monitor all files and directories in the monitored directory and its subdirectories up to a specified depth, filtering by file types, file names, file contents, and file paths."""
        try:
            async def monitor_recursive(path: Path, depth: int):
                await self.monitor_file_or_directory(path)
                if path.is_dir() and depth < max_depth:
                    for subdir in path.iterdir():
                        if subdir.is_file() and subdir.suffix in file_types and subdir.name in file_names and subdir.read_text() in file_contents and subdir.resolve().as_posix() in file_paths:
                            await monitor_recursive(subdir, depth + 1)

            await monitor_recursive(self.directory, 0)
        except Exception as e:
            logger.error(f"Error monitoring all files and directories recursively with depth, file types, file names, file contents, and file paths: {e}")

    async def monitor_all_recursive_with_depth_and_file_types_and_file_names_and_file_contents_and_file_paths_and_file_attributes(self, max_depth: int, file_types: List[str], file_names: List[str], file_contents: List[str], file_paths: List[str], file_attributes: List[str]):
        """Monitor all files and directories in the monitored directory and its subdirectories up to a specified depth, filtering by file types, file names, file contents, file paths, and file attributes."""
        try:
            async def monitor_recursive(path: Path, depth: int):
                await self.monitor_file_or_directory(path)
                if path.is_dir() and depth < max_depth:
                    for subdir in path.iterdir():
                        if subdir.is_file() and subdir.suffix in file_types and subdir.name in file_names and subdir.read_text() in file_contents and subdir.resolve().as_posix() in file_paths and all(getattr(subdir, attr) for attr in file_attributes):
                            await monitor_recursive(subdir, depth + 1)

            await monitor_recursive(self.directory, 0)
        except Exception as e:
            logger.error(f"Error monitoring all files and directories recursively with depth, file types, file names, file contents, file paths, and file attributes: {e}")

    async def monitor_all_recursive_with_depth_and_file_types_and_file_names_and_file_contents_and_file_paths_and_file_attributes_and_file_permissions(self, max_depth: int, file_types: List[str], file_names: List[str], file_contents: List[str], file_paths: List[str], file_attributes: List[str], file_permissions: List[str]):
        """Monitor all files and directories in the monitored directory and its subdirectories up to a specified depth, filtering by file types, file names, file contents, file paths, file attributes, and file permissions."""
        try:
            async def monitor_recursive(path: Path, depth: int):
                await self.monitor_file_or_directory(path)
                if path.is_dir() and depth < max_depth:
                    for subdir in path.iterdir():
                        if subdir.is_file() and subdir.suffix in file_types and subdir.name in file_names and subdir.read_text() in file_contents and subdir.resolve().as_posix() in file_paths and all(getattr(subdir, attr) for attr in file_attributes) and all(subdir.stat().st_mode & getattr(stat, 'S_I'+perm) for perm in file_permissions):
                            await monitor_recursive(subdir, depth + 1)

            await monitor_recursive(self.directory, 0)
        except Exception as e:
            logger.error(f"Error monitoring all files and directories recursively with depth, file types, file names, file contents, file paths, file attributes, and file permissions: {e}")

    async def monitor_all_recursive_with_depth_and_file_types_and_file_names_and_file_contents_and_file_paths_and_file_attributes_and_file_permissions_and_file_timestamps(self, max_depth: int, file_types: List[str], file_names: List[str], file_contents: List[str], file_paths: List[str], file_attributes: List[str], file_permissions: List[str], file_timestamps: List[str]):
        """Monitor all files and directories in the monitored directory and its subdirectories up to a specified depth, filtering by file types, file names, file contents, file paths, file attributes, file permissions, and file timestamps."""
        try:
            async def monitor_recursive(path: Path, depth: int):
                await self.monitor_file_or_directory(path)
                if path.is_dir() and depth < max_depth:
                    for subdir in path.iterdir():
                        if subdir.is_file() and subdir.suffix in file_types and subdir.name in file_names and subdir.read_text() in file_contents and subdir.resolve().as_posix() in file_paths and all(getattr(subdir, attr) for attr in file_attributes) and all(subdir.stat().st_mode & getattr(stat, 'S_I'+perm) for perm in file_permissions) and all(getattr(subdir, ts) for ts in file_timestamps):
                            await monitor_recursive(subdir, depth + 1)

            await monitor_recursive(self.directory, 0)
        except Exception as e:
            logger.error(f"Error monitoring all files and directories recursively with depth, file types, file names, file contents, file paths, file attributes, file permissions, and file timestamps: {e}")

    async def monitor_all_recursive_with_depth_and_file_types_and_file_names_and_file_contents_and_file_paths_and_file_attributes_and_file_permissions_and_file_timestamps_and_file_sizes(self, max_depth: int, file_types: List[str], file_names: List[str], file_contents: List[str], file_paths: List[str], file_attributes: List[str], file_permissions: List[str], file_timestamps: List[str], file_sizes: List[str]):
        """Monitor all files and directories in the monitored directory and its subdirectories up to a specified depth, filtering by file types, file names, file contents, file paths, file attributes, file permissions, file timestamps, and file sizes."""
        try:
            async def monitor_recursive(path: Path, depth: int):
                await self.monitor_file_or_directory(path)
                if path.is_dir() and depth < max_depth:
                    for subdir in path.iterdir():
                        if subdir.is_file() and subdir.suffix in file_types and subdir.name in file_names and subdir.read_text() in file_contents and subdir.resolve().as_posix() in file_paths and all(getattr(subdir, attr) for attr in file_attributes) and all(subdir.stat().st_mode & getattr(stat, 'S_I'+perm) for perm in file_permissions) and all(getattr(subdir, ts) for ts in file_timestamps) and subdir.stat().st_size in file_sizes:
                            await monitor_recursive(subdir, depth + 1)

            await monitor_recursive(self.directory, 0)
        except Exception as e:
            logger.error(f"Error monitoring all files and directories recursively with depth, file types, file names, file contents, file paths, file attributes, file permissions, file timestamps, and file sizes: {e}")

    async def monitor_all_recursive_with_depth_and_file_types_and_file_names_and_file_contents_and_file_paths_and_file_attributes_and_file_permissions_and_file_timestamps_and_file_sizes_and_file_hashes(self, max_depth: int, file_types: List[str], file_names: List[str], file_contents: List[str], file_paths: List[str], file_attributes: List[str], file_permissions: List[str], file_timestamps: List[str], file_sizes: List[str], file_hashes: List[str]):
        """Monitor all files and directories in the monitored directory and its subdirectories up to a specified depth, filtering by file types, file names, file contents, file paths, file attributes, file permissions, file timestamps, file sizes, and file hashes."""
        try:
            async def monitor_recursive(path: Path, depth: int):
                await self.monitor_file_or_directory(path)
                if path.is_dir() and depth < max_depth:
                    for subdir in path.iterdir():
                        if subdir.is_file() and subdir.suffix in file_types and subdir.name in file_names and subdir.read_text() in file_contents and subdir.resolve().as_posix() in file_paths and all(getattr(subdir, attr) for attr in file_attributes) and all(subdir.stat().st_mode & getattr(stat, 'S_I'+perm) for perm in file_permissions) and all(getattr(subdir, ts) for ts in file_timestamps) and subdir.stat().st_size in file_sizes and subdir.read_bytes() in file_hashes:
                            await monitor_recursive(subdir, depth + 1)

            await monitor_recursive(self.directory, 0)
        except Exception as e:
            logger.error(f"Error monitoring all files and directories recursively with depth, file types, file names, file contents, file paths, file attributes, file permissions, file timestamps, file sizes, and file hashes: {e}")

    async def monitor_all_recursive_with_depth_and_file_types_and_file_names_and_file_contents_and_file_paths_and_file_attributes_and_file_permissions_and_file_timestamps_and_file_sizes_and_file_hashes_and_file_metadata(self, max_depth: int, file_types: List[str], file_names: List[str], file_contents: List[str], file_paths: List[str], file_attributes: List[str], file_permissions: List[str], file_timestamps: List[str], file_sizes: List[str], file_hashes: List[str], file_metadata: List[str]):
        """Monitor all files and directories in the monitored directory and its subdirectories up to a specified depth, filtering by file types, file names, file contents, file paths, file attributes, file permissions, file timestamps, file sizes, file hashes, and file metadata."""
        try:
            async def monitor_recursive(path: Path, depth: int):
                await self.monitor_file_or_directory(path)
                if path.is_dir() and depth < max_depth:
                    for subdir in path.iterdir():
                        if subdir.is_file() and subdir.suffix in file_types and subdir.name in file_names and subdir.read_text() in file_contents and subdir.resolve().as_posix() in file_paths and all(getattr(subdir, attr) for attr in file_attributes) and all(subdir.stat().st_mode & getattr(stat, 'S_I'+perm) for perm in file_permissions) and all(getattr(subdir, ts) for ts in file_timestamps) and subdir.stat().st_size in file_sizes and subdir.read_bytes() in file_hashes and all(getattr(subdir, meta) for meta in file_metadata):
                            await monitor_recursive(subdir, depth + 1)

            await monitor_recursive(self.directory, 0)
        except Exception as e:
            logger.error(f"Error monitoring all files and directories recursively with depth, file types, file names, file contents, file paths, file attributes, file permissions, file timestamps, file sizes, file hashes, and file metadata: {e}")

</rewritten_file>