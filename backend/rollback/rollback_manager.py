# backend/src/rollback/rollback_manager.py

import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional

from backend.config.settings import (
    DATA_DIR,  # Ensure settings provide configurable options if desired.
)
from backend.utils.async_io import AsyncFileIO

logger = logging.getLogger(__name__)

# Define directories for trash and backup
TRASH_DIR = Path("trash")
TRASH_DIR.mkdir(exist_ok=True)
BACKUP_DIR = Path("backup/rollback_temp")
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

ROLLBACK_LOG_FILE = DATA_DIR / "rollback.json"


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
class RollbackOperation:
    """
    Represents a single file operation that can be undone.
    """

    def __init__(
        self,
        operation: str,
        source: str,
        destination: Optional[str] = None,
        timestamp: Optional[float] = None,
        backup: Optional[str] = None,
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
        self.backup = backup

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "operation": self.operation,
            "source": self.source,
            "destination": self.destination,
            "backup": self.backup,
        }

    @staticmethod
    def from_dict(data: Dict) -> "RollbackOperation":
        return RollbackOperation(
            operation=data["operation"],
            source=data["source"],
            destination=data.get("destination"),
            timestamp=data.get("timestamp"),
            backup=data.get("backup"),
        )


class RollbackManager:
    """
    Manages file operations for rollback and redo functionality.

    Enhancements include:
      • Asynchronous backup, move, and deletion operations using AsyncFileIO.
      • A singleton design to share one rollback manager instance across the project.
      • Enhanced logging with retry details and configurable options.
      • Configurable trash retention for cleanup.
    """

    _instance = None

    @staticmethod
    def get_instance():
        if RollbackManager._instance is None:
            RollbackManager._instance = RollbackManager()
        return RollbackManager._instance

    def __init__(self, rollback_log: Path = ROLLBACK_LOG_FILE):
        self.rollback_log = rollback_log
        self._undo_stack: List[RollbackOperation] = []
        self._redo_stack: List[RollbackOperation] = []
        self.rollback_log.parent.mkdir(parents=True, exist_ok=True)
        if not self.rollback_log.exists():
            self.rollback_log.write_text("[]", encoding="utf-8")
        self.max_retries = 3  # Configurable max retry attempts.
        self.trash_retention = 604800  # Default: 7 days in seconds.
        # Load any existing operations asynchronously.
        asyncio.run(self._load_from_file_async())

    async def _load_from_file_async(self):
        data = await AsyncFileIO.read_json(self.rollback_log)
        if not isinstance(data, list):
            data = []
        for entry in data:
            op = RollbackOperation.from_dict(entry)
            self._undo_stack.append(op)
        logger.info(f"Loaded {len(data)} rollback entries into memory.")

    async def _append_to_file(self, op: RollbackOperation):
        data = await AsyncFileIO.read_json(self.rollback_log)
        if not isinstance(data, list):
            data = []
        data.append(op.to_dict())
        await AsyncFileIO.write_json(self.rollback_log, data)

    async def _backup_file(self, file_path: Path) -> Optional[Path]:
        """
        Creates an asynchronous backup copy of the file using AsyncFileIO.
        """
        if not file_path.exists():
            logger.warning(f"Backup failed: Source file {file_path} does not exist.")
            return None
        try:
            backup_file = BACKUP_DIR / f"{file_path.name}.{int(time.time())}.bak"
            success = await AsyncFileIO.copy(file_path, backup_file)
            if success:
                logger.info(f"Backup created for {file_path} at {backup_file}")
                return backup_file
            else:
                logger.error(f"Backup failed for {file_path}")
                return None
        except Exception as e:
            logger.error(f"Error backing up file {file_path}: {e}")
            return None

    async def record_operation(
        self, operation: str, source: str, destination: Optional[str] = None
    ) -> None:
        """
        Records a new file operation for rollback. For deletion and modification,
        a backup copy is stored asynchronously.
        """
        op_type = operation.lower()
        backup = None
        src_path = Path(source)
        if op_type in ("delete", "modify"):
            backup_obj = await self._backup_file(src_path)
            backup = str(backup_obj) if backup_obj else None
        op = RollbackOperation(operation, source, destination, backup=backup)
        self._undo_stack.append(op)
        self._redo_stack.clear()
        logger.info(
            f"Recorded operation: {op.operation} | {op.source} -> {op.destination}"
        )
        await self._append_to_file(op)

    async def restore_from_trash(self, file_name: str) -> bool:
        """
        Asynchronously restores a file from the trash directory to the current working directory.
        """
        trashed_file = TRASH_DIR / file_name
        if not trashed_file.exists():
            logger.error(f"Restore failed: {trashed_file} does not exist in trash.")
            return False
        restore_path = Path.cwd() / file_name
        try:
            # For move, we simulate by copying then deleting the trashed file.
            success = await AsyncFileIO.copy(trashed_file, restore_path)
            if success:
                await asyncio.to_thread(trashed_file.unlink)
                logger.info(f"Restored {trashed_file} to {restore_path}")
                return True
            else:
                logger.error(f"Failed to restore {trashed_file} from trash.")
                return False
        except Exception as e:
            logger.error(f"Error restoring {trashed_file}: {e}")
            return False

    async def clear_trash(self) -> None:
        """
        Empties the trash directory by deleting files older than the configured retention period.
        """
        now = time.time()

        async def _delete_file(file: Path):
            if file.is_file() and now - file.stat().st_mtime > self.trash_retention:
                try:
                    await asyncio.to_thread(file.unlink)
                    logger.info(f"Deleted trashed file: {file}")
                except Exception as e:
                    logger.error(f"Error deleting {file} from trash: {e}")

        tasks = [_delete_file(file) for file in TRASH_DIR.iterdir()]
        await asyncio.gather(*tasks)

    async def undo_last_operation(self) -> bool:
        """
        Asynchronously undoes the most recent operation using retry logic.
        """
        if not self._undo_stack:
            logger.warning("No operations to undo.")
            return False

        op = self._undo_stack.pop()
        logger.info(f"Attempting to undo operation: {op.operation} on {op.source}")
        attempt = 0
        while attempt < self.max_retries:
            try:
                await self._reverse_operation(op)
                self._redo_stack.append(op)
                logger.info(f"Undo successful for {op.operation} on {op.source}")
                return True
            except Exception as e:
                attempt += 1
                logger.error(
                    f"Error reversing operation {op.operation} (attempt {attempt}): {e}"
                )
                await asyncio.sleep(1)
        logger.error(
            f"Failed to reverse operation after {self.max_retries} attempts: {op.operation} on {op.source}"
        )
        self._undo_stack.append(op)
        return False

    async def redo_last_undone(self) -> bool:
        """
        Asynchronously redoes the last undone operation.
        """
        if not self._redo_stack:
            logger.warning("No operations to redo.")
            return False

        op = self._redo_stack.pop()
        logger.info(f"Attempting to redo operation: {op.operation} on {op.source}")
        try:
            if op.operation.lower() == "modify":
                backup_path = Path(op.backup) if op.backup else None
                if backup_path and backup_path.exists():
                    success = await AsyncFileIO.copy(backup_path, Path(op.source))
                    if success:
                        self._undo_stack.append(op)
                        logger.info(
                            f"Redo: Restored file {op.source} from backup {backup_path}"
                        )
                        return True
                    else:
                        logger.error("No backup available for redo.")
                        return False
                else:
                    logger.error("No backup available for redo.")
                    return False
            else:
                await self._apply_operation(op)
                self._undo_stack.append(op)
                logger.info(f"Redo successful for {op.operation} on {op.source}")
                return True
        except Exception as e:
            logger.error(f"Redo failed for {op.source}: {e}")
            self._redo_stack.append(op)
            return False

    async def cleanup_old_entries(self, retention_days: float = 7.0) -> None:
        """
        Asynchronously removes rollback log entries older than the retention period.
        """
        cutoff_time = time.time() - (retention_days * 86400)
        data = await AsyncFileIO.read_json(self.rollback_log)
        if not isinstance(data, list):
            data = []
        new_data = [entry for entry in data if entry.get("timestamp", 0) >= cutoff_time]
        await AsyncFileIO.write_json(self.rollback_log, new_data)
        logger.info(f"Cleaned up rollback entries older than {retention_days} days.")

    async def _move(self, source: Path, destination: Path) -> None:
        """
        An asynchronous helper to move a file by copying it via AsyncFileIO and then deleting the source.
        """
        success = await AsyncFileIO.copy(source, destination)
        if success:
            await asyncio.to_thread(source.unlink)
            logger.info(f"Moved {source} -> {destination}")
        else:
            raise Exception(f"Failed to move {source} to {destination}")

    async def _reverse_operation(self, op: RollbackOperation) -> None:
        """
        Asynchronously reverses an operation with proper error handling and verification.
        """
        op_type = op.operation.lower()
        src = Path(op.source)
        dest = Path(op.destination) if op.destination else None

        if op_type == "delete":
            if src.exists():
                trashed_file = TRASH_DIR / src.name
                await self._move(src, trashed_file)
                logger.info(f"Moved deleted file {src} to trash at {trashed_file}")
            else:
                logger.info(f"File {src} not found; may have already been moved.")
        elif op_type in ("move", "rename"):
            if dest and dest.exists():
                await self._move(dest, src)
                if src.exists():
                    logger.info(
                        f"Reversed {op_type} operation: Moved {dest} back to {src}"
                    )
                else:
                    raise Exception(
                        "Verification failed: File not found at source after move."
                    )
            else:
                logger.warning(
                    f"Destination {dest} does not exist; cannot reverse {op_type} operation."
                )
        elif op_type == "modify":
            backup_path = Path(op.backup) if op.backup else None
            if backup_path and backup_path.exists():
                success = await AsyncFileIO.copy(backup_path, src)
                if success:
                    logger.info(
                        f"Restored modified file {src} from backup {backup_path}"
                    )
                else:
                    raise Exception(
                        f"Failed to restore file {src} from backup {backup_path}"
                    )
            else:
                logger.warning(f"No backup found for modified file {src}")
        elif op_type == "create":
            if src.exists():
                await asyncio.to_thread(src.unlink)
                logger.info(f"Reversed creation by deleting file {src}")
            else:
                logger.info(f"File {src} already deleted.")
        else:
            raise Exception(f"No reverse logic implemented for operation '{op_type}'.")

    async def _apply_operation(self, op: RollbackOperation) -> None:
        """
        Asynchronously re-applies an operation as recorded.
        """
        op_type = op.operation.lower()
        src = Path(op.source)
        dest = Path(op.destination) if op.destination else None

        if op_type in ("move", "rename"):
            if src.exists() and dest is not None:
                await self._move(src, dest)
                logger.info(f"Re-applied move: {src} -> {dest}")
        elif op_type == "delete":
            if src.exists():
                await asyncio.to_thread(src.unlink)
                logger.info(f"Re-applied delete on {src}")
        elif op_type == "create":
            raise Exception(
                "Redo for 'create' operation is not supported without stored file data."
            )
        else:
            raise Exception(f"No apply logic implemented for operation '{op_type}'.")


# Create a singleton instance for the entire project.
rollback_manager = RollbackManager.get_instance()
