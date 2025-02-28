import asyncio
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DirectoryManager:
    """Handles directory creation and validation with async operations."""

    @staticmethod
    async def ensure_directory(directory: Path):
        """Ensures that a directory exists asynchronously."""
        try:
            await asyncio.to_thread(directory.mkdir, parents=True, exist_ok=True)
            logger.info(f"Ensured directory exists: {directory}")
        except Exception as e:
            logger.error(f"Error ensuring directory {directory}: {e}")

    @staticmethod
    async def cleanup_empty_dirs(directory: Path):
        """Recursively removes empty directories asynchronously."""

        async def remove_if_empty(subdir: Path):
            if subdir.is_dir() and not any(subdir.iterdir()):
                try:
                    await asyncio.to_thread(subdir.rmdir)
                    logger.info(f"Removed empty directory: {subdir}")
                except Exception as e:
                    logger.error(f"Failed to remove {subdir}: {e}")

        for subdir in directory.glob("**/"):
            await remove_if_empty(subdir)
