"""File system monitoring and event handling for The Aichemist Codex."""

import asyncio
import logging
import threading
import time
from pathlib import Path
from typing import Any, NoReturn

from watchdog.events import FileSystemEvent, FileSystemEventHandler

from the_aichemist_codex.infrastructure.config.loader.config_loader import config
from the_aichemist_codex.infrastructure.fs.changes import ChangeDetector
from the_aichemist_codex.infrastructure.fs.operations import FileMover
from the_aichemist_codex.infrastructure.fs.rules import RulesEngine

logger = logging.getLogger(__name__)


# TODO: These components need to be fully migrated
# Temporary implementations until the migration is complete
class TemporaryRollbackManager:
    def create_rollback_point(self, file_path: Path) -> None:
        logger.warning(
            f"RollbackManager.create_rollback_point not fully migrated: {file_path}"
        )


class TemporaryChangeHistoryManager:
    def record_creation(self, file_path: Path) -> None:
        logger.warning(
            f"ChangeHistoryManager.record_creation not fully migrated: {file_path}"
        )

    def record_modification(self, file_path: Path) -> None:
        logger.warning(
            f"ChangeHistoryManager.record_modification not fully migrated: {file_path}"
        )

    def record_deletion(self, file_path: Path) -> None:
        logger.warning(
            f"ChangeHistoryManager.record_deletion not fully migrated: {file_path}"
        )

    def record_move(self, src_path: Path, dest_path: Path) -> None:
        logger.warning(
            f"ChangeHistoryManager.record_move not fully migrated: "
            f"{src_path} -> {dest_path}"
        )


class TemporaryVersionManager:
    def create_version(self, file_path: Path) -> None:
        logger.warning(f"VersionManager.create_version not fully migrated: {file_path}")


# Temporary implementations until migration is complete
rollback_manager = TemporaryRollbackManager()
change_history_manager = TemporaryChangeHistoryManager()
version_manager = TemporaryVersionManager()


# Create a proper subclass instead of monkey patching
class EnhancedChangeDetector(ChangeDetector):
    """
    Enhanced version of ChangeDetector with additional tracking capabilities.
    Temporary implementation until these features are
    fully integrated into the main class.
    """

    def __init__(self) -> None:
        super().__init__()
        self._file_cache: dict[str, dict[str, Any]] = {}

    def is_tracked_file(self, file_path: Path) -> bool:
        """
        Check if a file is being tracked.

        Args:
            file_path: Path to the file

        Returns:
            bool: True if the file is tracked, False otherwise
        """
        return str(file_path) in self._file_cache

    def add_file(self, file_path: Path) -> None:
        """
        Add a file to the tracking cache.

        Args:
            file_path: Path to the file
        """
        self._file_cache[str(file_path)] = {"first_seen": time.time()}

    def remove_file(self, file_path: Path) -> None:
        """
        Remove a file from the tracking cache.

        Args:
            file_path: Path to the file
        """
        if str(file_path) in self._file_cache:
            del self._file_cache[str(file_path)]

    def update_file_path(self, old_path: Path, new_path: Path) -> None:
        """
        Update the path of a tracked file.

        Args:
            old_path: Original path of the file
            new_path: New path of the file
        """
        if str(old_path) in self._file_cache:
            self._file_cache[str(new_path)] = self._file_cache[str(old_path)]
            del self._file_cache[str(old_path)]


# Create an instance for use
change_detector = EnhancedChangeDetector()


# Common utilities needed by the event handler
def is_file_being_processed(file_path: Path) -> bool:
    """
    Check if a file is currently being processed.

    Args:
        file_path: Path to the file

    Returns:
        bool: True if the file is being processed, False otherwise
    """
    # Temporary implementation until migration is complete
    return False


def mark_file_as_processing(file_path: Path) -> None:
    """
    Mark a file as being processed.

    Args:
        file_path: Path to the file
    """
    # Temporary implementation until migration is complete
    pass


def mark_file_as_done_processing(file_path: Path) -> None:
    """
    Mark a file as done processing.

    Args:
        file_path: Path to the file
    """
    # Temporary implementation until migration is complete
    pass


class FileEventHandler(FileSystemEventHandler):
    def __init__(self, base_directory: Path) -> None:
        self.base_directory = base_directory.resolve()
        self.file_mover = FileMover(self.base_directory)
        self.rules_engine = RulesEngine()
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

        # Convert to string first to ensure type compatibility
        file_path = Path(str(event.src_path)).resolve()
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

        # Convert to string first to ensure type compatibility
        file_path = Path(str(event.src_path)).resolve()

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

        # Convert to string first to ensure type compatibility
        file_path = Path(str(event.src_path)).resolve()
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

        # Convert to string first to ensure type compatibility
        src_path = Path(str(event.src_path)).resolve()
        dest_path = Path(str(event.dest_path)).resolve()
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
            # TODO: RulesEngine does not have the same API as RuleBasedSorter
            # For now, we'll just log the operation
            logger.debug(f"Applying rules to {file_path}")
            # Uncomment when the method is implemented:
            # await self.rules_engine.apply_rules(file_path)

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

    while True:
        try:
            # Run sorting operations
            logger.debug("Running scheduled sorting")
            # TODO: Implement RulesEngine usage for scheduled sorting:
            # rules_engine = RulesEngine(Path(config.get("base_directory", ".")))
            # rules_engine.apply_scheduled_sorting()
            logger.debug("Scheduled sorting complete")
        except Exception as e:
            logger.error(f"Error in scheduled sorting: {e}")

        # Sleep until next run
        time.sleep(config.get("scheduled_sorting_interval", 3600))  # Default: 1 hour
