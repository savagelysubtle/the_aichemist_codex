import asyncio
import logging
from pathlib import Path

from backend.src.rollback.rollback_manager import RollbackManager

logger = logging.getLogger(__name__)
rollback_manager = RollbackManager()


class DirectoryManager:
    """Handles directory creation and validation with async operations."""

    @staticmethod
    async def ensure_directory(directory: Path):
        """Ensures that a directory exists asynchronously and records a rollback for creation if it was newly made."""
        directory = directory.resolve()

        # Use async existence check
        dir_exists = await asyncio.to_thread(directory.exists)

        if not dir_exists:
            try:
                await asyncio.to_thread(directory.mkdir, parents=True, exist_ok=True)
                logger.info(f"Ensured directory exists: {directory}")
                # Record the creation so that an undo would delete this new directory.
                # Use the async version of record_operation
                await rollback_manager.record_operation("create", str(directory))
            except Exception as e:
                logger.error(f"Error ensuring directory {directory}: {e}")
        else:
            logger.debug(f"Directory already exists: {directory}")

    @staticmethod
    async def cleanup_empty_dirs(directory: Path):
        """Recursively removes empty directories asynchronously and records a rollback for each deletion."""
        directory = directory.resolve()

        async def remove_if_empty(subdir: Path):
            # Check if directory exists and is empty
            is_dir = await asyncio.to_thread(subdir.is_dir)
            if not is_dir:
                return

            # Check if directory is empty (convert to list to properly evaluate)
            dir_contents = await asyncio.to_thread(lambda: list(subdir.iterdir()))
            if not dir_contents:
                try:
                    # Record deletion before removing the directory.
                    await rollback_manager.record_operation("delete", str(subdir))
                    await asyncio.to_thread(subdir.rmdir)
                    logger.info(f"Removed empty directory: {subdir}")
                except Exception as e:
                    logger.error(f"Failed to remove {subdir}: {e}")

        # Get all subdirectories
        subdirs = await asyncio.to_thread(lambda: list(directory.glob("**/")))

        # Process each subdirectory
        for subdir in subdirs:
            await remove_if_empty(subdir)
