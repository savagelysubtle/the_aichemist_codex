# backend/src/file_manager/file_watcher.py

import asyncio
import logging
import os
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from src.config.config_loader import config
from src.file_manager.file_mover import FileMover
from src.file_manager.sorter import RuleBasedSorter
from src.rollback.rollback_manager import RollbackManager
from src.utils.safety import SafeFileHandler

logger = logging.getLogger(__name__)
rollback_manager = RollbackManager()


class FileEventHandler(FileSystemEventHandler):
    def __init__(self, base_directory: Path):
        self.base_directory = base_directory
        self.file_mover = FileMover(base_directory)
        self.debounce_timer = None
        self.debounce_interval = 2  # seconds

    def on_created(self, event):
        if event.is_directory:
            return
        file_path = Path(event.src_path)
        if SafeFileHandler.should_ignore(file_path):
            logger.info(f"Skipping ignored file: {file_path}")
            return
        logger.info(f"New file detected: {file_path}")
        if self.debounce_timer:
            self.debounce_timer.cancel()
        self.debounce_timer = threading.Timer(
            self.debounce_interval, self.process_file, args=[file_path]
        )
        self.debounce_timer.start()

    def on_modified(self, event):
        if event.is_directory:
            return
        file_path = Path(event.src_path)
        if SafeFileHandler.should_ignore(file_path):
            logger.info(f"Skipping modification for ignored file: {file_path}")
            return
        logger.info(f"External modification detected: {file_path}")
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(
                rollback_manager.record_operation("modify", str(file_path))
            )
        except RuntimeError:
            asyncio.run(rollback_manager.record_operation("modify", str(file_path)))

    def process_file(self, file_path: Path):
        try:
            rule_applied = self.file_mover.apply_rules(file_path)
            if not rule_applied and file_path.exists():
                target_dir = self.file_mover.auto_folder_structure(file_path)
                FileMover.move_file(file_path, target_dir / file_path.name)
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")


def monitor_directory():
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

    sorter = RuleBasedSorter()

    def scheduled_sorting():
        while True:
            for path in paths_to_watch:
                sorter.sort_directory(Path(path))
            time.sleep(config.get("sorting_interval", 300))

    threading.Thread(target=scheduled_sorting, daemon=True).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping file monitoring...")
        for observer in observers:
            observer.stop()
        for observer in observers:
            observer.join()
