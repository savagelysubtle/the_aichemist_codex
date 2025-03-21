"""File system monitoring and event handling for The Aichemist Codex."""

import asyncio
import logging
import threading
import time
from pathlib import Path
from typing import NoReturn

from watchdog.events import FileSystemEvent, FileSystemEventHandler

from the_aichemist_codex.backend.config.loader.config_loader import config
from the_aichemist_codex.backend.file_manager.change_detector import ChangeDetector
from the_aichemist_codex.backend.file_manager.change_history_manager import (
    change_history_manager,
)
from the_aichemist_codex.backend.file_manager.common import (
    is_file_being_processed,
    mark_file_as_done_processing,
    mark_file_as_processing,
)
from the_aichemist_codex.backend.file_manager.file_mover import FileMover
from the_aichemist_codex.backend.file_manager.sorter import RuleBasedSorter
from the_aichemist_codex.backend.file_manager.version_manager import version_manager
from the_aichemist_codex.backend.rollback.rollback_manager import RollbackManager

logger = logging.getLogger(__name__)
rollback_manager = RollbackManager()
change_detector = ChangeDetector()


class FileEventHandler(FileSystemEventHandler):
    def __init__(self, base_directory: Path) -> None:
        self.base_directory = base_directory.resolve()
        self.file_mover = FileMover(self.base_directory)
        self.sorter = RuleBasedSorter(self.base_directory)
        self.debounce_interval = config.get("file_manager.debounce_interval", 1)
        self.processing_lock = threading.Lock()
        self.last_processed = {}

    def on_created(self, event: FileSystemEvent) -> None:
        """
        Handle file creation events.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        file_path = Path(event.src_path).resolve()
        logger.debug(f"File created: {file_path}")

        # Skip temporary files
        if self._is_temporary_file(file_path):
            return

        # Check if this is a new file or one we're tracking
        if not change_detector.is_tracked_file(file_path):
            change_detector.add_file(file_path)
            change_history_manager.record_creation(file_path)

        # Process the file
        self.process_file(file_path)

    def on_modified(self, event: FileSystemEvent) -> None:
        """
        Handle file modification events.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        file_path = Path(event.src_path).resolve()

        # Skip temporary files
        if self._is_temporary_file(file_path):
            return

        # Debounce rapid modifications
        current_time = time.time()
        if file_path in self.last_processed:
            time_diff = current_time - self.last_processed[file_path]
            if time_diff < self.debounce_interval:
                return

        self.last_processed[file_path] = current_time
        logger.debug(f"File modified: {file_path}")

        # Record the change
        if change_detector.is_tracked_file(file_path):
            change_history_manager.record_modification(file_path)

        # Process the file
        self.process_file(file_path)

    def on_deleted(self, event: FileSystemEvent) -> None:
        """
        Handle file deletion events.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        file_path = Path(event.src_path).resolve()
        logger.debug(f"File deleted: {file_path}")

        # Record the deletion
        if change_detector.is_tracked_file(file_path):
            change_history_manager.record_deletion(file_path)
            change_detector.remove_file(file_path)

    def on_moved(self, event: FileSystemEvent) -> None:
        """
        Handle file move events.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        src_path = Path(event.src_path).resolve()
        dest_path = Path(event.dest_path).resolve()
        logger.debug(f"File moved: {src_path} -> {dest_path}")

        # Skip temporary files
        if self._is_temporary_file(src_path) or self._is_temporary_file(dest_path):
            return

        # Record the move
        if change_detector.is_tracked_file(src_path):
            change_history_manager.record_move(src_path, dest_path)
            change_detector.update_file_path(src_path, dest_path)

        # Process the destination file
        self.process_file(dest_path)

    async def _analyze_change(self, file_path: Path) -> None:
        """
        Analyze a file change asynchronously.

        Args:
            file_path: Path to the file
        """
        try:
            # Check if file still exists
            if not file_path.exists():
                logger.debug(f"File no longer exists: {file_path}")
                return

            # Create a version snapshot
            version_manager.create_version(file_path)

            # Apply rules based on file type and content
            await self.sorter.apply_rules_async(file_path)

            # Update metadata
            # This would typically involve extracting and storing metadata
            # about the file, such as MIME type, creation date, etc.
            # For now, we'll just log that we're doing it
            logger.debug(f"Updating metadata for {file_path}")

            # Check for duplicates
            # This would involve comparing the file against known files
            # to identify potential duplicates
            # For now, we'll just log that we're doing it
            logger.debug(f"Checking for duplicates of {file_path}")

        except Exception as e:
            logger.error(f"Error analyzing change for {file_path}: {e}")
            # Create rollback point in case of error
            rollback_manager.create_rollback_point(file_path)

    def process_file(self, file_path: Path) -> None:
        """
        Process a file after a change event.

        Args:
            file_path: Path to the file
        """
        # Skip if file is already being processed
        if is_file_being_processed(file_path):
            logger.debug(f"File already being processed: {file_path}")
            return

        # Mark file as being processed
        with self.processing_lock:
            mark_file_as_processing(file_path)

        try:
            # Run async analysis in a separate thread
            asyncio.run(self._analyze_change(file_path))
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
        finally:
            # Mark file as done processing
            with self.processing_lock:
                mark_file_as_done_processing(file_path)

    def _is_temporary_file(self, file_path: Path) -> bool:
        """
        Check if a file is a temporary file.

        Args:
            file_path: Path to the file

        Returns:
            bool: True if the file is temporary, False otherwise
        """
        # Check file name patterns that indicate temporary files
        name = file_path.name.lower()
        return (
            name.startswith("~")
            or name.startswith(".")
            or name.endswith(".tmp")
            or name.endswith(".temp")
            or ".tmp." in name
            or "._mp_" in name
        )


def monitor_directory() -> None:
    """Start monitoring the configured directories."""
    # This function is called from the main application to start monitoring
    # We'll use the directory_monitor singleton from the module that imports this
    # This avoids the circular import
    logger.info("Directory monitoring started")


def scheduled_sorting() -> NoReturn:
    """Run scheduled sorting operations in the background."""
    logger.info("Starting scheduled sorting thread")
    sorter = RuleBasedSorter(Path(config.get("base_directory", ".")))

    while True:
        try:
            # Run sorting operations
            logger.debug("Running scheduled sorting")
            # This would typically involve applying rules to files
            # based on a schedule, rather than in response to events
            # For now, we'll just log that we're doing it
            logger.debug("Scheduled sorting complete")
        except Exception as e:
            logger.error(f"Error in scheduled sorting: {e}")

        # Sleep until next run
        time.sleep(config.get("scheduled_sorting_interval", 3600))  # Default: 1 hour
