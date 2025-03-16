"""File system monitoring and event handling for The Aichemist Codex."""

import asyncio
import logging
import threading
import time
from pathlib import Path
from typing import NoReturn

from watchdog.events import FileSystemEvent, FileSystemEventHandler

from backend.src.config.config_loader import config
from backend.src.file_manager.change_detector import ChangeDetector
from backend.src.file_manager.change_history_manager import change_history_manager
from backend.src.file_manager.directory_monitor import directory_monitor
from backend.src.file_manager.file_mover import FileMover
from backend.src.file_manager.sorter import RuleBasedSorter
from backend.src.file_manager.version_manager import version_manager
from backend.src.rollback.rollback_manager import RollbackManager
from backend.src.utils.safety import SafeFileHandler

logger = logging.getLogger(__name__)
rollback_manager = RollbackManager()
change_detector = ChangeDetector()


class FileEventHandler(FileSystemEventHandler):
    def __init__(self, base_directory: Path) -> None:
        self.base_directory = base_directory.resolve()
        self.file_mover = FileMover(self.base_directory)
        self.debounce_timer = None
        self.debounce_interval = 2  # seconds
        # Get version control settings
        self.auto_version = config.get("versioning", {}).get(
            "auto_create_versions", True
        )
        self.version_on_modify = config.get("versioning", {}).get(
            "version_on_modify", True
        )
        logger.info(f"FileEventHandler initialized for {self.base_directory}")

    def on_created(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        file_path = Path(str(event.src_path)).resolve()
        if SafeFileHandler.should_ignore(file_path):
            logger.info(f"Skipping ignored file: {file_path}")
            return

        logger.info(f"New file detected: {file_path}")

        # Record the creation for potential rollback
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(
                rollback_manager.record_operation("create", str(file_path))
            )
            # Analyze the change using the ChangeDetector
            loop.create_task(self._analyze_change(file_path))
        except RuntimeError:
            # If no event loop is running, create one
            asyncio.run(rollback_manager.record_operation("create", str(file_path)))
            # We'll handle change detection in the debounce process

        # Cancel previous timer if one exists
        if self.debounce_timer:
            self.debounce_timer.cancel()

        # Set a new timer to process the file after debounce interval
        self.debounce_timer = threading.Timer(
            self.debounce_interval, self.process_file, args=[file_path]
        )
        self.debounce_timer.start()
        logger.debug(f"Debounce timer started for {file_path}")

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        file_path = Path(str(event.src_path)).resolve()
        if SafeFileHandler.should_ignore(file_path):
            logger.info(f"Skipping modification for ignored file: {file_path}")
            return

        logger.info(f"External modification detected: {file_path}")

        try:
            # Record the modification for potential rollback
            loop = asyncio.get_running_loop()
            loop.create_task(
                rollback_manager.record_operation("modify", str(file_path))
            )
            # Analyze the change
            loop.create_task(self._analyze_change(file_path))

            # Create a version if enabled
            if self.auto_version and self.version_on_modify:
                loop.create_task(
                    version_manager.create_version(
                        file_path,
                        change_reason="Auto-saved on external modification",
                        author="System",
                    )
                )
        except RuntimeError:
            # If no event loop is running, create one
            asyncio.run(rollback_manager.record_operation("modify", str(file_path)))

    def on_deleted(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        file_path = Path(str(event.src_path)).resolve()
        if SafeFileHandler.should_ignore(file_path):
            logger.info(f"Skipping deletion for ignored file: {file_path}")
            return

        logger.info(f"File deletion detected: {file_path}")

        try:
            # Record the deletion for potential recovery
            loop = asyncio.get_running_loop()
            loop.create_task(
                rollback_manager.record_operation("delete", str(file_path))
            )
        except RuntimeError:
            # If no event loop is running, create one
            asyncio.run(rollback_manager.record_operation("delete", str(file_path)))

    def on_moved(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        src_path = Path(str(event.src_path)).resolve()
        dest_path = Path(str(event.dest_path)).resolve()

        if SafeFileHandler.should_ignore(src_path) or SafeFileHandler.should_ignore(
            dest_path
        ):
            logger.info(f"Skipping move for ignored file: {src_path} -> {dest_path}")
            return

        logger.info(f"File moved: {src_path} -> {dest_path}")

        try:
            # Record the move for potential rollback
            loop = asyncio.get_running_loop()
            loop.create_task(
                rollback_manager.record_operation("move", str(src_path), str(dest_path))
            )

            # Create a version of the file in its new location if enabled
            if self.auto_version:
                loop.create_task(
                    version_manager.create_version(
                        dest_path,
                        change_reason=f"Auto-saved after move from {src_path.name}",
                        author="System",
                    )
                )
        except RuntimeError:
            # If no event loop is running, create one
            asyncio.run(
                rollback_manager.record_operation("move", str(src_path), str(dest_path))
            )

    async def _analyze_change(self, file_path: Path) -> None:
        """
        Analyze a file change using the ChangeDetector.

        This method:
        1. Detects the type and severity of the change
        2. Records the change in the history database
        3. Creates a version of the file if configured to do so
        """
        if not file_path.exists():
            logger.debug(f"Cannot analyze non-existent file: {file_path}")
            return

        try:
            # Analyze with change detector
            change_info = await change_detector.detect_change(file_path)
            if change_info:
                # Record the change in history
                await change_history_manager.record_change(change_info)

                # Create a version for significant changes if auto-versioning is enabled
                if (
                    self.auto_version
                    and change_info.change_type == "CONTENT"
                    and change_info.severity in ("MAJOR", "CRITICAL")
                ):
                    await version_manager.create_version(
                        file_path,
                        change_reason=f"Auto-saved after {change_info.severity.lower()} content change",
                        author="System",
                    )

                logger.info(
                    f"Change analyzed and recorded for {file_path}: "
                    f"{change_info.change_type} ({change_info.severity})"
                )
        except Exception as e:
            logger.error(f"Error analyzing change for {file_path}: {e}")

    def process_file(self, file_path: Path) -> None:
        """Process a file after the debounce period."""
        if not file_path.exists():
            logger.debug(f"Cannot process non-existent file: {file_path}")
            return

        try:
            # Apply FileMover rules to sort the file
            moved_path = asyncio.run(self.file_mover.apply_rules(file_path))

            if moved_path and isinstance(moved_path, Path) and moved_path != file_path:
                logger.info(f"File processed and moved to {moved_path}")

                # Create a version of the sorted file if enabled
                if self.auto_version:
                    asyncio.run(
                        version_manager.create_version(
                            moved_path,
                            change_reason="Auto-saved after sorting",
                            author="System",
                        )
                    )
            else:
                logger.debug(f"File processed but not moved: {file_path}")

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")


def monitor_directory() -> None:
    """Start monitoring directories for file changes."""
    # Delegate to the DirectoryMonitor
    directory_monitor.start()


# Define a thread for scheduled sorting
def scheduled_sorting() -> NoReturn:
    """Periodically run sorting on directories."""
    while True:
        try:
            # Get directories to sort
            directories = config.get("monitoring", {}).get("directories", [])

            for directory in directories:
                try:
                    path = Path(directory).expanduser().resolve()
                    if path.exists() and path.is_dir():
                        sorter = RuleBasedSorter()
                        asyncio.run(sorter.sort_directory(path))
                except Exception as e:
                    logger.error(f"Error sorting directory {directory}: {e}")

            # Sleep until next sort interval
            interval = config.get("monitoring", {}).get("sorting_interval_minutes", 60)
            time.sleep(interval * 60)
        except Exception as e:
            logger.error(f"Error in scheduled sorting: {e}")
            # Don't crash the thread, just wait and retry
            time.sleep(60)
