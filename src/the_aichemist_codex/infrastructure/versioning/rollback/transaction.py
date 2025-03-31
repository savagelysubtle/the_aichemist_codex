"""Transaction support for rollback operations.

This module provides functionality for atomic rollback operations, ensuring
that either all files are successfully rolled back or none are.
"""

import datetime
import logging
import os
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from the_aichemist_codex.infrastructure.config.settings import determine_project_root
from the_aichemist_codex.infrastructure.utils.io.async_io import AsyncFileIO

from ..version_manager import version_manager
from .engine import RollbackSpec, RollbackStrategy, rollback_engine

logger = logging.getLogger(__name__)


class TransactionState(Enum):
    """States of a rollback transaction."""

    CREATED = "created"  # Transaction created but not started
    PREPARING = "preparing"  # Preparing the rollback operations
    STAGING = "staging"  # Staging the rollback operations
    COMMITTING = "committing"  # Committing the rollback operations
    ROLLING_BACK = "rolling_back"  # Rolling back the transaction
    COMPLETED = "completed"  # Transaction completed successfully
    FAILED = "failed"  # Transaction failed
    ABORTED = "aborted"  # Transaction aborted manually


@dataclass
class TransactionMetadata:
    """Metadata for a rollback transaction."""

    transaction_id: str
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    completed_at: datetime.datetime | None = None
    state: TransactionState = TransactionState.CREATED
    specs: list[RollbackSpec] = field(default_factory=list)
    description: str = ""
    initiator: str = ""
    error_message: str = ""


class TransactionManager:
    """Manages atomic transactions for rollback operations."""

    def __init__(self):
        """Initialize the transaction manager."""
        self.file_io = AsyncFileIO()
        self.project_root = determine_project_root()
        self.transactions_dir = self.project_root / "data" / "transactions"

        # Ensure directories exist
        self.transactions_dir.mkdir(parents=True, exist_ok=True)

        # Active transactions
        self._active_transactions: dict[str, TransactionMetadata] = {}

    async def create_transaction(
        self, specs: list[RollbackSpec], description: str = "", initiator: str = ""
    ) -> TransactionMetadata:
        """Create a new rollback transaction.

        Args:
            specs: List of rollback specifications
            description: Optional description of the transaction
            initiator: Optional identifier of the initiator

        Returns:
            Metadata for the new transaction
        """
        # Generate a transaction ID
        transaction_id = (
            f"tx_{uuid.uuid4().hex[:8]}_{int(datetime.datetime.now().timestamp())}"
        )

        # Create metadata
        metadata = TransactionMetadata(
            transaction_id=transaction_id,
            specs=specs,
            description=description,
            initiator=initiator,
        )

        # Store the metadata
        self._active_transactions[transaction_id] = metadata
        await self._save_transaction_metadata(metadata)

        logger.info(
            f"Created transaction {transaction_id} with {len(specs)} operations"
        )
        return metadata

    async def prepare_transaction(self, transaction_id: str) -> tuple[bool, str | None]:
        """Prepare a transaction by validating all operations.

        Args:
            transaction_id: ID of the transaction to prepare

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Get the transaction metadata
            metadata = await self._get_transaction(transaction_id)
            if not metadata:
                return False, f"Transaction {transaction_id} not found"

            # Update state
            metadata.state = TransactionState.PREPARING
            await self._save_transaction_metadata(metadata)

            # Validate each operation
            all_valid = True
            errors = []

            for spec in metadata.specs:
                # Validate that the file exists
                if (
                    not os.path.exists(spec.file_path)
                    and spec.strategy != RollbackStrategy.COPY
                ):
                    errors.append(f"File does not exist: {spec.file_path}")
                    all_valid = False
                    continue

                # Check if the version exists
                (
                    version_file,
                    version_metadata,
                ) = await version_manager.get_version(spec.file_path, spec.version_id)

                if not version_file or not version_metadata:
                    errors.append(
                        f"Version {spec.version_id} not found for {spec.file_path}"
                    )
                    all_valid = False

            # Update state based on validation
            if all_valid:
                metadata.state = TransactionState.STAGING
                await self._save_transaction_metadata(metadata)
                return True, None
            else:
                metadata.state = TransactionState.FAILED
                error_message = "Validation failed: " + "; ".join(errors)
                metadata.error_message = error_message
                await self._save_transaction_metadata(metadata)
                return False, error_message

        except Exception as e:
            logger.error(f"Error preparing transaction {transaction_id}: {e}")
            if metadata:
                metadata.state = TransactionState.FAILED
                metadata.error_message = str(e)
                await self._save_transaction_metadata(metadata)
            return False, str(e)

    async def commit_transaction(self, transaction_id: str) -> tuple[bool, str | None]:
        """Commit a prepared transaction.

        Args:
            transaction_id: ID of the transaction to commit

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Get the transaction metadata
            metadata = await self._get_transaction(transaction_id)
            if not metadata:
                return False, f"Transaction {transaction_id} not found"

            # Check if the transaction is in the right state
            if metadata.state != TransactionState.STAGING:
                return (
                    False,
                    f"Transaction {transaction_id} is not ready to commit (state: {metadata.state.value})",
                )

            # Update state
            metadata.state = TransactionState.COMMITTING
            await self._save_transaction_metadata(metadata)

            # Perform the rollback operations
            bulk_result = await rollback_engine.rollback_bulk(
                metadata.specs, transaction=True
            )

            if bulk_result.success:
                # Update state
                metadata.state = TransactionState.COMPLETED
                metadata.completed_at = datetime.datetime.now()
                await self._save_transaction_metadata(metadata)
                return True, None
            else:
                # Update state
                metadata.state = TransactionState.FAILED
                metadata.error_message = bulk_result.error_message
                await self._save_transaction_metadata(metadata)
                return False, bulk_result.error_message

        except Exception as e:
            logger.error(f"Error committing transaction {transaction_id}: {e}")
            if metadata:
                metadata.state = TransactionState.FAILED
                metadata.error_message = str(e)
                await self._save_transaction_metadata(metadata)
            return False, str(e)

    async def abort_transaction(
        self, transaction_id: str, reason: str = ""
    ) -> tuple[bool, str | None]:
        """Abort a transaction.

        Args:
            transaction_id: ID of the transaction to abort
            reason: Optional reason for aborting

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Get the transaction metadata
            metadata = await self._get_transaction(transaction_id)
            if not metadata:
                return False, f"Transaction {transaction_id} not found"

            # Check if the transaction can be aborted
            if metadata.state in [TransactionState.COMPLETED, TransactionState.FAILED]:
                return (
                    False,
                    f"Cannot abort transaction {transaction_id} in state {metadata.state.value}",
                )

            # Update state
            metadata.state = TransactionState.ABORTED
            metadata.error_message = reason
            metadata.completed_at = datetime.datetime.now()
            await self._save_transaction_metadata(metadata)

            return True, None

        except Exception as e:
            logger.error(f"Error aborting transaction {transaction_id}: {e}")
            return False, str(e)

    async def get_transaction_status(
        self, transaction_id: str
    ) -> tuple[TransactionMetadata | None, str | None]:
        """Get the status of a transaction.

        Args:
            transaction_id: ID of the transaction to check

        Returns:
            Tuple of (transaction_metadata, error_message)
        """
        try:
            # Get the transaction metadata
            metadata = await self._get_transaction(transaction_id)
            if not metadata:
                return None, f"Transaction {transaction_id} not found"

            return metadata, None

        except Exception as e:
            logger.error(f"Error getting transaction status for {transaction_id}: {e}")
            return None, str(e)

    async def list_transactions(
        self, state: TransactionState | None = None, limit: int = 100
    ) -> list[TransactionMetadata]:
        """List transactions, optionally filtered by state.

        Args:
            state: Optional state to filter by
            limit: Maximum number of transactions to return

        Returns:
            List of transaction metadata
        """
        try:
            transactions = []

            # List transaction files
            tx_files = list(self.transactions_dir.glob("*.json"))
            tx_files.sort(key=os.path.getmtime, reverse=True)

            # Limit the number of files to process
            tx_files = tx_files[:limit]

            # Load each transaction
            for tx_file in tx_files:
                try:
                    json_data = await self.file_io.read_json(tx_file)

                    # Convert the data to a TransactionMetadata object
                    metadata = await self._dict_to_metadata(json_data)

                    # Apply filter if provided
                    if state is None or metadata.state == state:
                        transactions.append(metadata)

                except Exception as e:
                    logger.error(f"Error loading transaction from {tx_file}: {e}")

            return transactions

        except Exception as e:
            logger.error(f"Error listing transactions: {e}")
            return []

    async def _get_transaction(self, transaction_id: str) -> TransactionMetadata | None:
        """Get a transaction by ID.

        Args:
            transaction_id: ID of the transaction

        Returns:
            Transaction metadata or None if not found
        """
        # Check active transactions first
        if transaction_id in self._active_transactions:
            return self._active_transactions[transaction_id]

        # Check the filesystem
        tx_path = self.transactions_dir / f"{transaction_id}.json"

        if not await self.file_io.exists(tx_path):
            return None

        try:
            json_data = await self.file_io.read_json(tx_path)
            return await self._dict_to_metadata(json_data)
        except Exception as e:
            logger.error(f"Error loading transaction {transaction_id}: {e}")
            return None

    async def _save_transaction_metadata(self, metadata: TransactionMetadata) -> bool:
        """Save transaction metadata to disk.

        Args:
            metadata: Transaction metadata to save

        Returns:
            True if successful, False otherwise
        """
        try:
            # Update in-memory cache
            self._active_transactions[metadata.transaction_id] = metadata

            # Convert to dict
            data = await self._metadata_to_dict(metadata)

            # Write to disk
            tx_path = self.transactions_dir / f"{metadata.transaction_id}.json"
            return await self.file_io.write_json(tx_path, data)

        except Exception as e:
            logger.error(
                f"Error saving transaction metadata for {metadata.transaction_id}: {e}"
            )
            return False

    async def _metadata_to_dict(self, metadata: TransactionMetadata) -> dict[str, Any]:
        """Convert transaction metadata to a dictionary.

        Args:
            metadata: Transaction metadata

        Returns:
            Dictionary representation of the metadata
        """
        data = {
            "transaction_id": metadata.transaction_id,
            "created_at": metadata.created_at.isoformat(),
            "completed_at": metadata.completed_at.isoformat()
            if metadata.completed_at
            else None,
            "state": metadata.state.value,
            "description": metadata.description,
            "initiator": metadata.initiator,
            "error_message": metadata.error_message,
            "specs": [],
        }

        # Convert specs
        for spec in metadata.specs:
            spec_data = {
                "file_path": str(spec.file_path),
                "version_id": spec.version_id,
                "strategy": spec.strategy.value,
                "backup_path": str(spec.backup_path) if spec.backup_path else None,
            }
            data["specs"].append(spec_data)

        return data

    async def _dict_to_metadata(self, data: dict[str, Any]) -> TransactionMetadata:
        """Convert a dictionary to transaction metadata.

        Args:
            data: Dictionary representation of metadata

        Returns:
            TransactionMetadata object
        """
        # Convert basic fields
        metadata = TransactionMetadata(
            transaction_id=data["transaction_id"],
            created_at=datetime.datetime.fromisoformat(data["created_at"]),
            completed_at=datetime.datetime.fromisoformat(data["completed_at"])
            if data["completed_at"]
            else None,
            state=TransactionState(data["state"]),
            description=data["description"],
            initiator=data["initiator"],
            error_message=data["error_message"],
        )

        # Convert specs
        for spec_data in data["specs"]:
            spec = RollbackSpec(
                file_path=Path(spec_data["file_path"]),
                version_id=spec_data["version_id"],
                strategy=RollbackStrategy(spec_data["strategy"]),
                backup_path=Path(spec_data["backup_path"])
                if spec_data["backup_path"]
                else None,
            )
            metadata.specs.append(spec)

        return metadata

    async def _apply_rollback(self, transaction: TransactionMetadata) -> bool:
        """Apply the rollback operation.

        Args:
            transaction: Transaction metadata

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            for spec in transaction.specs:
                result = await rollback_engine.rollback_file(
                    spec.file_path, spec.version_id, strategy=spec.strategy
                )
                if not result.success:
                    transaction.error_message = (
                        f"Failed to rollback file: {spec.file_path}"
                    )
                    return False

            # Create version for the rollback if all successful
            if transaction.state == TransactionState.COMPLETED:
                # Create version for each file individually
                for spec in transaction.specs:
                    await version_manager.create_version(
                        spec.file_path,
                        manual=True,
                        annotation=f"Rollback: {transaction.description}",
                        tags=[
                            "rollback",
                            f"transaction-{transaction.transaction_id[:8]}",
                        ],
                    )
            return True
        except Exception as e:
            logger.error(f"Error during rollback application: {str(e)}")
            return False


# Create a singleton instance for application-wide use
transaction_manager = TransactionManager()
