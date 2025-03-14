import asyncio
import logging
from pathlib import Path

from backend.rollback.rollback_manager import RollbackManager

logger = logging.getLogger(__name__)
rollback_manager = RollbackManager()


class DirectoryManager:
    """Handles directory creation and validation with async operations."""

    @staticmethod
    async def ensure_directory(directory: Path):
        """Ensures that a directory exists asynchronously and records a rollback for creation if it was newly made."""
        if not directory.exists():
            try:
                await asyncio.to_thread(directory.mkdir, parents=True, exist_ok=True)
                logger.info(f"Ensured directory exists: {directory}")
                # Record the creation so that an undo would delete this new directory.
                rollback_manager.record_operation("create", str(directory))
            except Exception as e:
                logger.error(f"Error ensuring directory {directory}: {e}")
        else:
            logger.info(f"Directory already exists: {directory}")

    @staticmethod
    async def cleanup_empty_dirs(directory: Path):
        """Recursively removes empty directories asynchronously and records a rollback for each deletion."""

        async def remove_if_empty(subdir: Path):
            if subdir.is_dir() and not any(subdir.iterdir()):
                try:
                    # Record deletion before removing the directory.
                    rollback_manager.record_operation("delete", str(subdir))
                    await asyncio.to_thread(subdir.rmdir)
                    logger.info(f"Removed empty directory: {subdir}")
                except Exception as e:
                    logger.error(f"Failed to remove {subdir}: {e}")

        for subdir in directory.glob("**/"):
            await remove_if_empty(subdir)
