"""Monitors directories and triggers file organization on changes."""

import logging
import os
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from aichemist_codex.config.config_loader import config
from aichemist_codex.file_manager.file_mover import FileMover

logger = logging.getLogger(__name__)


class FileEventHandler(FileSystemEventHandler):
    """Handles file events and triggers file movement rules."""

    def __init__(self, base_directory: Path):
        self.file_mover = FileMover(base_directory)

    def on_created(self, event):
        """Triggered when a file is created in the watched directory."""
        if not event.is_directory:
            file_path = Path(event.src_path)
            logger.info(f"New file detected: {file_path}")
            self.file_mover.apply_rules(file_path)


def monitor_directory():
    """Starts monitoring directories for file changes."""
    paths_to_watch = config.get("directories_to_watch", [])
    if not paths_to_watch:
        logger.warning("No directories specified for monitoring.")
        return

    observers = []
    for path in paths_to_watch:
        if not os.path.exists(path):
            logger.warning(f"Skipping non-existent path: {path}")
            continue

        event_handler = FileEventHandler(Path(path))
        observer = Observer()
        observer.schedule(event_handler, path, recursive=True)
        observer.start()
        observers.append(observer)
        logger.info(f"Monitoring started on: {path}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping file monitoring...")
        for observer in observers:
            observer.stop()
        for observer in observers:
            observer.join()
