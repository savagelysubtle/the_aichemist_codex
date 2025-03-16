"""File system monitoring and event handling for The Aichemist Codex."""

import asyncio
import logging
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from backend.src.config.config_loader import config
from backend.src.file_manager.file_mover import FileMover
from backend.src.file_manager.sorter import RuleBasedSorter
from backend.src.rollback.rollback_manager import RollbackManager
from backend.src.utils.safety import SafeFileHandler

logger = logging.getLogger(__name__)
rollback_manager = RollbackManager()


class FileEventHandler(FileSystemEventHandler):
    def __init__(self, base_directory: Path):
        self.base_directory = base_directory.resolve()
        self.file_mover = FileMover(self.base_directory)
        self.debounce_timer = None
        self.debounce_interval = 2  # seconds
        logger.info(f"FileEventHandler initialized for {self.base_directory}")

    def on_created(self, event):
        if event.is_directory:
            return
        file_path = Path(str(event.src_path)).resolve()
        if SafeFileHandler.should_ignore(file_path):
            logger.info(f"Skipping ignored file: {file_path}")
            return

        logger.info(f"New file detected: {file_path}")

        # Cancel previous timer if one exists
        if self.debounce_timer:
            self.debounce_timer.cancel()

        # Set a new timer to process the file after debounce interval
        self.debounce_timer = threading.Timer(
            self.debounce_interval, self.process_file, args=[file_path]
        )
        self.debounce_timer.start()
        logger.debug(f"Debounce timer started for {file_path}")

    def on_modified(self, event):
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
            logger.debug(f"Modification recorded for {file_path}")
        except RuntimeError:
            # If no event loop is running, create one
            asyncio.run(rollback_manager.record_operation("modify", str(file_path)))
            logger.debug(f"Modification recorded synchronously for {file_path}")

    def process_file(self, file_path: Path):
        """Process a file based on rules or auto-organization."""
        try:
            logger.info(f"Processing file: {file_path}")

            # First try to apply configured rules
            rule_applied = asyncio.run(self.file_mover.apply_rules(file_path))

            # If no rule matched and the file still exists, use auto-organization
            if not rule_applied and file_path.exists():
                logger.info(f"No rule matched for {file_path}, using auto-organization")
                target_dir = asyncio.run(
                    self.file_mover.auto_folder_structure(file_path)
                )
                asyncio.run(FileMover.move_file(file_path, target_dir / file_path.name))
                logger.info(f"File moved to {target_dir / file_path.name}")
            elif rule_applied:
                logger.info(f"Rule successfully applied to {file_path}")
            else:
                logger.warning(f"File no longer exists: {file_path}")
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            import traceback

            logger.debug(f"Traceback: {traceback.format_exc()}")


def monitor_directory():
    paths_to_watch = config.get("directories_to_watch", [])
    if not paths_to_watch:
        logger.warning("No directories specified for monitoring.")
        return

    observers = []
    for path_str in paths_to_watch:
        # Convert to Path object and resolve to absolute path
        path = Path(path_str).resolve()

        if not path.exists():
            logger.warning(f"Skipping non-existent path: {path}")
            continue

        logger.info(f"Setting up monitoring for: {path}")
        event_handler = FileEventHandler(path)
        observer = Observer()
        observer.schedule(event_handler, str(path), recursive=True)
        observer.start()
        observers.append(observer)
        logger.info(f"Monitoring started on: {path}")

    sorter = RuleBasedSorter()

    def scheduled_sorting():
        while True:
            for path_str in paths_to_watch:
                path = Path(path_str).resolve()
                if path.exists():
                    try:
                        sorter.sort_directory_sync(path)
                    except Exception as e:
                        logger.error(f"Error during scheduled sorting of {path}: {e}")
            time.sleep(config.get("sorting_interval", 300))

    sorting_thread = threading.Thread(target=scheduled_sorting, daemon=True)
    sorting_thread.start()
    logger.info("Scheduled sorting started")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping file monitoring...")
        for observer in observers:
            observer.stop()
        for observer in observers:
            observer.join()
        logger.info("File monitoring stopped")
