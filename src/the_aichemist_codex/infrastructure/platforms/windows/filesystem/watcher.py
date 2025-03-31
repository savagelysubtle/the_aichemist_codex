"""
File System Watcher - Monitors directories for changes and triggers events.
"""

import logging
import os
import threading
import time
from collections.abc import Callable
from enum import Enum
from pathlib import Path

# For Windows-specific implementation
if os.name == "nt":
    try:
        import win32con
        import win32file

        WINDOWS_API_AVAILABLE = True
    except ImportError:
        WINDOWS_API_AVAILABLE = False
else:
    WINDOWS_API_AVAILABLE = False


class FileEvent(Enum):
    """Enum representing file system events."""

    CREATED = 1
    MODIFIED = 2
    DELETED = 3
    RENAMED = 4


class FileWatcher:
    """Watches for file system changes and triggers callbacks."""

    def __init__(self, polling_interval: float = 1.0):
        """
        Initialize the file watcher.

        Args:
            polling_interval: Time in seconds between polling checks (for fallback method)
        """
        self.logger = logging.getLogger(__name__)
        self.polling_interval = polling_interval
        self.watched_paths: dict[Path, list[Callable]] = {}
        self.running = False
        self.watch_thread: threading.Thread | None = None

        # For polling implementation
        self.last_modified_times: dict[Path, float] = {}
        self.existing_files: dict[Path, set[Path]] = {}

    def start(self):
        """Start the file watching thread."""
        if self.running:
            return

        self.running = True

        if WINDOWS_API_AVAILABLE:
            self.watch_thread = threading.Thread(
                target=self._watch_windows, daemon=True
            )
        else:
            self.watch_thread = threading.Thread(
                target=self._watch_polling, daemon=True
            )

        self.watch_thread.start()
        self.logger.info(
            f"File watcher started using {'Windows API' if WINDOWS_API_AVAILABLE else 'polling'} method"
        )

    def stop(self):
        """Stop the file watching thread."""
        self.running = False
        if self.watch_thread:
            self.watch_thread.join(timeout=2.0)
            self.watch_thread = None
        self.logger.info("File watcher stopped")

    def watch(
        self, path: str | Path, callback: Callable[[FileEvent, Path], None]
    ) -> bool:
        """
        Add a path to watch.

        Args:
            path: Directory path to watch
            callback: Function to call when changes occur

        Returns:
            True if successfully added to watch list
        """
        dir_path = Path(path)

        if not dir_path.is_dir():
            self.logger.error(f"Cannot watch non-directory path: {dir_path}")
            return False

        if dir_path not in self.watched_paths:
            self.watched_paths[dir_path] = []

            # Initialize file list for polling method
            if not WINDOWS_API_AVAILABLE:
                self.existing_files[dir_path] = self._scan_directory(dir_path)
                self._update_modified_times(dir_path)

        self.watched_paths[dir_path].append(callback)
        self.logger.info(f"Now watching directory: {dir_path}")
        return True

    def unwatch(self, path: str | Path, callback: Callable | None = None) -> bool:
        """
        Remove a path from watch list.

        Args:
            path: Directory path to unwatch
            callback: Specific callback to remove (if None, removes all callbacks)

        Returns:
            True if successfully removed
        """
        dir_path = Path(path)

        if dir_path not in self.watched_paths:
            return False

        if callback is None:
            # Remove all watchers for this path
            del self.watched_paths[dir_path]
            if not WINDOWS_API_AVAILABLE and dir_path in self.existing_files:
                del self.existing_files[dir_path]
                del self.last_modified_times[dir_path]
        else:
            # Remove specific callback
            if callback in self.watched_paths[dir_path]:
                self.watched_paths[dir_path].remove(callback)

            # If no callbacks left, remove the path
            if not self.watched_paths[dir_path]:
                del self.watched_paths[dir_path]
                if not WINDOWS_API_AVAILABLE and dir_path in self.existing_files:
                    del self.existing_files[dir_path]
                    del self.last_modified_times[dir_path]

        self.logger.info(f"Stopped watching directory: {dir_path}")
        return True

    def _scan_directory(self, dir_path: Path) -> set[Path]:
        """Scan a directory and return set of all files."""
        files = set()
        try:
            for item in dir_path.rglob("*"):
                if item.is_file():
                    files.add(item)
        except Exception as e:
            self.logger.error(f"Error scanning directory {dir_path}: {e}")
        return files

    def _update_modified_times(self, dir_path: Path):
        """Update the last modified times for all files in directory."""
        for file_path in self.existing_files.get(dir_path, set()):
            try:
                self.last_modified_times[file_path] = file_path.stat().st_mtime
            except Exception:
                # File might have been deleted
                pass

    def _watch_polling(self):
        """Watch for changes using polling method."""
        while self.running:
            for dir_path in list(self.watched_paths.keys()):
                if not dir_path.exists():
                    continue

                # Get current files
                current_files = self._scan_directory(dir_path)
                previous_files = self.existing_files.get(dir_path, set())

                # Check for new and deleted files
                new_files = current_files - previous_files
                deleted_files = previous_files - current_files

                # Check for modified files
                modified_files = set()
                for file_path in current_files:
                    if file_path in self.last_modified_times:
                        try:
                            current_mtime = file_path.stat().st_mtime
                            if current_mtime > self.last_modified_times[file_path]:
                                modified_files.add(file_path)
                                self.last_modified_times[file_path] = current_mtime
                        except Exception:
                            # File might have been deleted
                            pass

                # Update file list
                self.existing_files[dir_path] = current_files

                # Update modified times for new files
                for file_path in new_files:
                    try:
                        self.last_modified_times[file_path] = file_path.stat().st_mtime
                    except Exception:
                        # File might have been deleted
                        pass

                # Remove deleted files from modified times
                for file_path in deleted_files:
                    if file_path in self.last_modified_times:
                        del self.last_modified_times[file_path]

                # Trigger callbacks
                for file_path in new_files:
                    self._trigger_callbacks(dir_path, FileEvent.CREATED, file_path)

                for file_path in modified_files:
                    self._trigger_callbacks(dir_path, FileEvent.MODIFIED, file_path)

                for file_path in deleted_files:
                    self._trigger_callbacks(dir_path, FileEvent.DELETED, file_path)

            # Sleep before next poll
            time.sleep(self.polling_interval)

    def _watch_windows(self):
        """Watch for changes using Windows API."""
        if not WINDOWS_API_AVAILABLE:
            self.logger.error("Windows API not available, falling back to polling")
            self._watch_polling()
            return

        # Dictionary to store directory handles and overlapped structures
        dir_handles = {}

        # Constants for the Windows API
        FILE_LIST_DIRECTORY = 0x0001
        FILE_NOTIFY_CHANGE_FILE_NAME = 0x00000001
        FILE_NOTIFY_CHANGE_DIR_NAME = 0x00000002
        FILE_NOTIFY_CHANGE_ATTRIBUTES = 0x00000004
        FILE_NOTIFY_CHANGE_SIZE = 0x00000008
        FILE_NOTIFY_CHANGE_LAST_WRITE = 0x00000010
        FILE_NOTIFY_CHANGE_CREATION = 0x00000040

        # Event mapping
        actions = {
            1: FileEvent.CREATED,
            2: FileEvent.DELETED,
            3: FileEvent.MODIFIED,
            4: FileEvent.RENAMED,
            5: FileEvent.RENAMED,
        }

        try:
            # Setup directory watches
            for dir_path in self.watched_paths.keys():
                try:
                    handle = win32file.CreateFile(
                        str(dir_path),
                        FILE_LIST_DIRECTORY,
                        win32con.FILE_SHARE_READ
                        | win32con.FILE_SHARE_WRITE
                        | win32con.FILE_SHARE_DELETE,
                        None,
                        win32con.OPEN_EXISTING,
                        win32con.FILE_FLAG_BACKUP_SEMANTICS
                        | win32con.FILE_FLAG_OVERLAPPED,
                        None,
                    )
                    dir_handles[dir_path] = handle
                except Exception as e:
                    self.logger.error(f"Error watching directory {dir_path}: {e}")

            # Main watch loop
            while self.running:
                # Process each watched directory
                for dir_path, handle in list(dir_handles.items()):
                    try:
                        results = win32file.ReadDirectoryChangesW(
                            handle,
                            1024,
                            True,  # Watch subtree
                            FILE_NOTIFY_CHANGE_FILE_NAME
                            | FILE_NOTIFY_CHANGE_DIR_NAME
                            | FILE_NOTIFY_CHANGE_ATTRIBUTES
                            | FILE_NOTIFY_CHANGE_SIZE
                            | FILE_NOTIFY_CHANGE_LAST_WRITE
                            | FILE_NOTIFY_CHANGE_CREATION,
                            None,
                            None,
                        )

                        for action, filename in results:
                            file_path = dir_path / filename
                            if action in actions:
                                event = actions[action]
                                self._trigger_callbacks(dir_path, event, file_path)

                    except Exception as e:
                        self.logger.error(f"Error reading changes for {dir_path}: {e}")

                # Small sleep to prevent CPU thrashing
                time.sleep(0.01)

        finally:
            # Clean up handles
            for handle in dir_handles.values():
                try:
                    handle.close()
                except Exception:
                    pass

    def _trigger_callbacks(self, dir_path: Path, event: FileEvent, file_path: Path):
        """Trigger all callbacks registered for a directory."""
        if dir_path not in self.watched_paths:
            return

        for callback in self.watched_paths[dir_path]:
            try:
                callback(event, file_path)
            except Exception as e:
                self.logger.error(f"Error in file watcher callback: {e}")
