"""Rollback manager for safe file operations.

Provides functionality to track file operations and roll them back
if needed, ensuring data integrity during file operations.
"""

import logging
import shutil
import uuid
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any

from ..config import get_config

logger = logging.getLogger(__name__)


class OperationType(Enum):
    """Type of file operation that can be tracked for rollback."""

    MOVE = auto()
    COPY = auto()
    RENAME = auto()
    DELETE = auto()
    CREATE = auto()
    MODIFY = auto()


class FileOperation:
    """Represents a single file operation that can be rolled back."""

    def __init__(
        self,
        operation_type: OperationType,
        affected_path: Path,
        original_state: Any = None,
        additional_info: dict[str, Any] | None = None,
    ):
        """
        Initialize a new file operation.

        Args:
            operation_type: Type of operation performed
            affected_path: Path to the file or directory affected
            original_state: Original state data (depends on operation type)
            additional_info: Any additional information needed for rollback
        """
        self.id = str(uuid.uuid4())
        self.operation_type = operation_type
        self.affected_path = affected_path
        self.timestamp = datetime.now()
        self.original_state = original_state
        self.additional_info = additional_info or {}
        self.rolled_back = False

    def __str__(self) -> str:
        """Return a string representation of the operation."""
        return (
            f"FileOperation(id={self.id}, type={self.operation_type.name}, "
            f"path='{self.affected_path}', timestamp={self.timestamp.isoformat()})"
        )


class RollbackManager:
    """
    Manages file operations and provides rollback functionality.

    This class tracks file operations in memory and provides the ability
    to roll back operations if needed. Operations can be grouped into
    transactions for atomicity.
    """

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(RollbackManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, backup_dir: Path | None = None):
        """
        Initialize the rollback manager.

        Args:
            backup_dir: Optional directory for storing backup files
        """
        # Only initialize once
        if RollbackManager._initialized:
            return

        # Set up backup directory
        if backup_dir is None:
            data_dir = Path(get_config("data_dir"))
            self.backup_dir = data_dir / ".backups"
        else:
            self.backup_dir = backup_dir

        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Initialize operation tracking
        self.operations: list[FileOperation] = []
        self.current_transaction_id: str | None = None
        self.transactions: dict[str, list[FileOperation]] = {}

        RollbackManager._initialized = True
        logger.debug(f"Rollback manager initialized with backup dir: {self.backup_dir}")

    def start_transaction(self) -> str:
        """
        Start a new transaction for grouping operations.

        Returns:
            str: Transaction ID
        """
        # End any existing transaction first
        if self.current_transaction_id:
            self.end_transaction()

        # Create a new transaction
        self.current_transaction_id = str(uuid.uuid4())
        self.transactions[self.current_transaction_id] = []

        logger.debug(f"Started transaction: {self.current_transaction_id}")
        return self.current_transaction_id

    def end_transaction(self) -> None:
        """End the current transaction."""
        if self.current_transaction_id:
            logger.debug(f"Ended transaction: {self.current_transaction_id}")
            self.current_transaction_id = None

    def _make_backup(self, file_path: Path) -> Path | None:
        """
        Create a backup of a file.

        Args:
            file_path: Path to the file to back up

        Returns:
            Optional[Path]: Path to the backup file, or None if backup failed
        """
        if not file_path.exists():
            logger.warning(f"Cannot back up non-existent file: {file_path}")
            return None

        # Create a unique backup filename
        backup_name = (
            f"{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            f"{file_path.suffix}"
        )
        backup_path = self.backup_dir / backup_name

        try:
            # Create the backup
            shutil.copy2(file_path, backup_path)
            logger.debug(f"Created backup of {file_path} at {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup of {file_path}: {e}")
            return None

    def record_operation(
        self, operation_type: OperationType, affected_path: Path, **kwargs
    ) -> FileOperation | None:
        """
        Record a file operation for potential rollback.

        Args:
            operation_type: Type of operation being performed
            affected_path: Path to the file or directory affected
            **kwargs: Additional information needed for rollback

        Returns:
            Optional[FileOperation]: The recorded operation, or None if recording failed
        """
        # Create a backup for relevant operations
        original_state = None
        if operation_type in (OperationType.MODIFY, OperationType.DELETE):
            if affected_path.exists() and affected_path.is_file():
                backup_path = self._make_backup(affected_path)
                if backup_path:
                    original_state = {"backup_path": backup_path}

        # Handle move and rename operations
        if operation_type in (OperationType.MOVE, OperationType.RENAME):
            # These require source and destination
            if "source" not in kwargs or "destination" not in kwargs:
                logger.error(
                    f"{operation_type.name} operation requires source and destination"
                )
                return None

        # Create operation record
        operation = FileOperation(
            operation_type=operation_type,
            affected_path=affected_path,
            original_state=original_state,
            additional_info=kwargs,
        )

        # Add to current transaction if one is active
        if self.current_transaction_id:
            self.transactions[self.current_transaction_id].append(operation)

        # Add to operations list
        self.operations.append(operation)

        logger.debug(f"Recorded operation: {operation}")
        return operation

    async def rollback_operation(self, operation: FileOperation) -> bool:
        """
        Roll back a single operation.

        Args:
            operation: The operation to roll back

        Returns:
            bool: True if successful
        """
        if operation.rolled_back:
            logger.warning(f"Operation already rolled back: {operation}")
            return True

        success = False

        try:
            # Rollback based on operation type
            if operation.operation_type == OperationType.DELETE:
                # Restore from backup
                if (
                    operation.original_state
                    and "backup_path" in operation.original_state
                ):
                    backup_path = Path(operation.original_state["backup_path"])
                    if backup_path.exists():
                        # Ensure parent directory exists
                        operation.affected_path.parent.mkdir(
                            parents=True, exist_ok=True
                        )
                        # Restore file
                        shutil.copy2(backup_path, operation.affected_path)
                        success = True

            elif operation.operation_type == OperationType.MODIFY:
                # Restore from backup
                if (
                    operation.original_state
                    and "backup_path" in operation.original_state
                ):
                    backup_path = Path(operation.original_state["backup_path"])
                    if backup_path.exists():
                        shutil.copy2(backup_path, operation.affected_path)
                        success = True

            elif (
                operation.operation_type == OperationType.MOVE
                or operation.operation_type == OperationType.RENAME
            ):
                # Move back to original location
                source = Path(operation.additional_info.get("destination", ""))
                destination = Path(operation.additional_info.get("source", ""))

                if source.exists() and destination.parent.exists():
                    # Ensure parent directory exists
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    # Move back
                    shutil.move(source, destination)
                    success = True

            elif operation.operation_type == OperationType.CREATE:
                # Delete the created file
                if operation.affected_path.exists():
                    if operation.affected_path.is_file():
                        operation.affected_path.unlink()
                    elif operation.affected_path.is_dir():
                        shutil.rmtree(operation.affected_path)
                    success = True

            else:
                logger.warning(
                    f"Unsupported operation type for rollback: {operation.operation_type}"
                )
                return False

            # Mark as rolled back if successful
            if success:
                operation.rolled_back = True
                logger.info(f"Successfully rolled back operation: {operation}")

            return success

        except Exception as e:
            logger.error(f"Error rolling back operation {operation}: {e}")
            return False

    async def rollback_transaction(self, transaction_id: str) -> bool:
        """
        Roll back all operations in a transaction.

        Args:
            transaction_id: ID of the transaction to roll back

        Returns:
            bool: True if all operations were rolled back successfully
        """
        if transaction_id not in self.transactions:
            logger.error(f"Transaction not found: {transaction_id}")
            return False

        # Roll back operations in reverse order
        operations = self.transactions[transaction_id]
        success = True

        for operation in reversed(operations):
            op_success = await self.rollback_operation(operation)
            if not op_success:
                success = False
                logger.error(
                    f"Failed to roll back operation in transaction {transaction_id}: {operation}"
                )

        return success

    async def rollback_last_operations(self, count: int = 1) -> bool:
        """
        Roll back the last n operations.

        Args:
            count: Number of operations to roll back

        Returns:
            bool: True if all operations were rolled back successfully
        """
        if not self.operations:
            logger.warning("No operations to roll back")
            return True

        # Get the last n operations
        to_rollback = self.operations[-count:]
        if len(to_rollback) < count:
            logger.warning(
                f"Requested to roll back {count} operations, but only {len(to_rollback)} available"
            )

        # Roll back in reverse order
        success = True
        for operation in reversed(to_rollback):
            op_success = await self.rollback_operation(operation)
            if not op_success:
                success = False

        return success

    def clear_history(self) -> None:
        """Clear operation history and transactions."""
        self.operations = []
        self.transactions = {}
        self.current_transaction_id = None
        logger.info("Cleared rollback history")


# Create a singleton instance
rollback_manager = RollbackManager()
