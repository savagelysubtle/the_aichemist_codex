import logging
import os
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from file_manager.rules_engine import apply_rules


class FileEventHandler(FileSystemEventHandler):
    """Custom event handler for monitoring and triggering file organization."""

    def __init__(self, rules, source_dir):
        self.rules = rules
        self.source_dir = source_dir

    def on_created(self, event):
        """Triggers file organization on new file creation."""
        if not event.is_directory:
            logging.info(f"File created: {event.src_path}")
            self._process_new_file(event.src_path)

    def _process_new_file(self, file_path):
        """Processes a newly created file."""
        try:
            logging.info(f"Processing new file: {file_path}")
            apply_rules(self.source_dir, self.rules)
        except Exception as e:
            logging.error(f"Error processing file {file_path}: {e}")


def monitor_directory(paths_to_watch, rules):
    """Starts monitoring the specified directories for file system events."""
    observers = []

    for path_to_watch in paths_to_watch:
        if not os.path.exists(path_to_watch):
            logging.error(f"Path does not exist: {path_to_watch}")
            continue

        event_handler = FileEventHandler(rules=rules, source_dir=path_to_watch)
        observer = Observer()
        observer.schedule(event_handler, path=path_to_watch, recursive=True)
        observer.start()
        observers.append(observer)
        logging.info(f"Monitoring started on: {path_to_watch}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Stopping all observers...")
        for observer in observers:
            observer.stop()
        for observer in observers:
            observer.join()
