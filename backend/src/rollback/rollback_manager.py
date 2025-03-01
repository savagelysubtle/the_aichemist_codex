# src/aichemist_codex/rollback/rollback_manager.py

import json
import logging
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional

from src.config.settings import DATA_DIR
from src.utils.safety import SafeFileHandler

logger = logging.getLogger(__name__)

# This file will store our rollback history in JSON form. Each entry represents one operation.
# Example entry structure:
# {
#    "timestamp": 1678450123.25,
#    "operation": "move",
#    "source": "/path/to/original_file.txt",
#    "destination": "/path/to/target_dir/original_file.txt"
# }
#
# Additional fields (e.g., "old_name", "new_name", "deleted", "created") can be included for rename, delete, create, etc.

ROLLBACK_LOG_FILE = DATA_DIR / "rollback.json"


class RollbackOperation:
    """
    Represents a single file operation that can be undone.
    """

    def __init__(
        self,
        operation: str,
        source: str,
        destination: Optional[str] = None,
        timestamp: float = None,
    ):
        """
        Args:
            operation: The type of file operation, e.g. "move", "delete", "create", "rename".
            source: The original path of the file or directory.
            destination: The resulting path if the file was moved/renamed. For deletions, can be None.
            timestamp: Time the operation occurred (epoch). Defaults to time.time().
        """
        self.operation = operation
        self.source = source
        self.destination = destination
        self.timestamp = timestamp or time.time()

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "operation": self.operation,
            "source": self.source,
            "destination": self.destination,
        }

    @staticmethod
    def from_dict(data: Dict) -> "RollbackOperation":
        return RollbackOperation(
            operation=data["operation"],
            source=data["source"],
            destination=data.get("destination"),
            timestamp=data.get("timestamp"),
        )


class RollbackManager:
    """
    Manages tracking of file operations and provides undo/redo functionality.

    Usage:
        # 1) Record new operation:
        rollback_manager.record_operation("move", "/path/old.txt", "/path/new.txt")

        # 2) Undo the last operation:
        rollback_manager.undo_last_operation()

        # 3) Redo an undone operation:
        rollback_manager.redo_last_undone()

        # 4) Periodically clean up old entries beyond a retention threshold (e.g., 7 days):
        rollback_manager.cleanup_old_entries(retention_days=7)
    """

    def __init__(self, rollback_log: Path = ROLLBACK_LOG_FILE):
        self.rollback_log = rollback_log
        self._undo_stack: List[RollbackOperation] = []
        self._redo_stack: List[RollbackOperation] = []

        # Ensure the rollback log file/directory exists.
        self.rollback_log.parent.mkdir(parents=True, exist_ok=True)
        if not self.rollback_log.exists():
            self.rollback_log.write_text("[]", encoding="utf-8")

        # Load any existing entries from file into memory. (Optional, or we can keep them on disk.)
        self._load_from_file()

    def record_operation(self, operation: str, source: str, destination: Optional[str] = None) -> None:
        """
        Records a new file operation for rollback. Clears the redo stack (since we have a new branch).

        Args:
            operation: The type of operation, e.g. "move", "delete", "create", or "rename".
            source: The path of the file or directory before the operation.
            destination: The path of the file or directory after the operation (if applicable).
        """
        op = RollbackOperation(operation, source, destination)
        self._undo_stack.append(op)
        self._redo_stack.clear()

        logger.info(f"Recorded operation: {op.operation} | {op.source} -> {op.destination}")

        # Append to the rollback.json file
        self._append_to_file(op)

    def undo_last_operation(self) -> bool:
        """
        Undo the most recent operation from the undo stack.
        Returns True if an operation was undone, False otherwise.
        """
        if not self._undo_stack:
            logger.warning("No operations to undo.")
            return False

        op = self._undo_stack.pop()
        logger.info(f"Attempting to undo operation: {op.operation} (src={op.source}).")

        try:
            self._reverse_operation(op)
            # Put the reversed op into the redo stack so we can redo if needed
            self._redo_stack.append(op)
            logger.info(f"Undo successful for {op.operation} on {op.source}")
            return True
        except Exception as e:
            logger.error(f"Failed to undo operation on {op.source}: {e}")
            # If undo failed, push it back so we don't lose it
            self._undo_stack.append(op)
            return False

    def redo_last_undone(self) -> bool:
        """
        Re-applies the last undone operation.
        Returns True if a redo was performed, False otherwise.
        """
        if not self._redo_stack:
            logger.warning("No operations to redo.")
            return False

        op = self._redo_stack.pop()
        logger.info(f"Attempting to redo operation: {op.operation} (src={op.source}).")

        try:
            self._apply_operation(op)
            # Put it back onto the undo stack
            self._undo_stack.append(op)
            logger.info(f"Redo successful for {op.operation} on {op.source}")
            return True
        except Exception as e:
            logger.error(f"Failed to redo operation on {op.source}: {e}")
            self._redo_stack.append(op)
            return False

    def cleanup_old_entries(self, retention_days: float = 7.0) -> None:
        """
        Removes rollback entries older than retention_days from the rollback_log.json.
        Adjust as needed for large logs or compliance regulations.

        Args:
            retention_days: Number of days to keep rollback entries.
        """
        cutoff_time = time.time() - (retention_days * 86400)

        try:
            data = self._read_all_from_file()
            original_count = len(data)

            # Filter out old entries
            new_data = [entry for entry in data if entry.get("timestamp", 0) >= cutoff_time]
            removed_count = original_count - len(new_data)

            # Overwrite file
            self.rollback_log.write_text(json.dumps(new_data, indent=2), encoding="utf-8")
            logger.info(f"Cleaned up {removed_count} old rollback entries older than {retention_days} days.")
        except Exception as e:
            logger.error(f"Error cleaning rollback entries: {e}")

    # ---------------------------
    # Internal Helpers
    # ---------------------------

    def _reverse_operation(self, op: RollbackOperation) -> None:
        """
        Given an operation, do the inverse.
        """
        operation = op.operation.lower()
        src = Path(op.source)
        dest = Path(op.destination) if op.destination else None

        if operation == "move" or operation == "rename":
            # Move it back from dest -> source
            if dest and dest.exists():
                logger.debug(f"Undoing move. Moving {dest} back to {src}")
                self._safe_move(dest, src)
        elif operation == "delete":
            # If file was deleted, we can't trivially restore it unless we physically store it in a backup
            # or send it to trash. If we had a "trash" or backup system, we’d restore from there.
            # For now, log a warning that undo is incomplete.
            logger.warning("Undo for 'delete' not implemented (no backup).")
        elif operation == "create":
            # If file was newly created, remove it
            if src.exists():
                logger.debug(f"Undoing create. Deleting {src}")
                self._safe_delete(src)
        else:
            logger.warning(f"No reverse logic implemented for operation '{operation}'.")

    def _apply_operation(self, op: RollbackOperation) -> None:
        """
        Re-do the operation as it was recorded.
        """
        operation = op.operation.lower()
        src = Path(op.source)
        dest = Path(op.destination) if op.destination else None

        if operation == "move" or operation == "rename":
            if src.exists() and dest is not None:
                logger.debug(f"Re-doing move. Moving {src} -> {dest}")
                self._safe_move(src, dest)
        elif operation == "delete":
            # If we truly want to re-delete, we can remove src if it still exists
            if src.exists():
                logger.debug(f"Re-doing delete. Deleting {src}")
                self._safe_delete(src)
        elif operation == "create":
            # We do not store the file’s contents, so redoing 'create' is partial or not feasible unless we do
            logger.warning("Cannot redo 'create' unless we store original file data.")
        else:
            logger.warning(f"No apply logic implemented for operation '{operation}'.")

    def _safe_move(self, source: Path, destination: Path) -> None:
        """
        Moves files or directories, ensuring no path is ignored or outside safe scope.
        """
        if SafeFileHandler.should_ignore(source):
            logger.warning(f"Ignoring move for file {source}, marked as ignored.")
            return

        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
            logger.info(f"Moved {source} -> {destination}")
        except Exception as e:
            logger.error(f"Failed to move {source} -> {destination}: {e}")
            raise

    def _safe_delete(self, file_path: Path) -> None:
        """
        Deletes a file or directory safely.
        """
        if SafeFileHandler.should_ignore(file_path):
            logger.warning(f"Ignoring delete for file {file_path}, marked as ignored.")
            return

        if file_path.is_dir():
            try:
                shutil.rmtree(file_path)
                logger.info(f"Deleted directory: {file_path}")
            except Exception as e:
                logger.error(f"Failed to delete directory {file_path}: {e}")
                raise
        else:
            try:
                file_path.unlink()
                logger.info(f"Deleted file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to delete file {file_path}: {e}")
                raise

    def _load_from_file(self):
        """
        Loads existing rollback operations from disk into the internal undo stack.
        You can adjust this logic if you prefer not to fully load them at startup.
        """
        try:
            data = self._read_all_from_file()
            for entry in data:
                op = RollbackOperation.from_dict(entry)
                self._undo_stack.append(op)
            logger.info(f"Loaded {len(data)} rollback entries into memory.")
        except Exception as e:
            logger.error(f"Error loading rollback log: {e}")

    def _append_to_file(self, op: RollbackOperation):
        """
        Appends a single operation to the rollback file.
        """
        try:
            data = self._read_all_from_file()
            data.append(op.to_dict())
            self.rollback_log.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Error writing rollback entry to file: {e}")

    def _read_all_from_file(self) -> List[Dict]:
        """
        Reads the entire rollback JSON log and returns it as a list of dicts.
        """
        try:
            raw = self.rollback_log.read_text(encoding="utf-8")
            return json.loads(raw)
        except Exception as e:
            logger.error(f"Error reading rollback log JSON: {e}")
            return []
