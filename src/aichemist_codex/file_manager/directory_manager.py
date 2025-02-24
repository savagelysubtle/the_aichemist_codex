"""Manages directory-related operations like creation and cleanup."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DirectoryManager:
    """Handles directory creation and validation."""

    @staticmethod
    def ensure_directory(directory: Path):
        """Ensures that a directory exists."""
        try:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured directory exists: {directory}")
        except Exception as e:
            logger.error(f"Error ensuring directory {directory}: {e}")

    @staticmethod
    def cleanup_empty_dirs(directory: Path):
        """Recursively removes empty directories."""
        for subdir in directory.glob("**/"):
            if subdir.is_dir() and not any(subdir.iterdir()):
                try:
                    subdir.rmdir()
                    logger.info(f"Removed empty directory: {subdir}")
                except Exception as e:
                    logger.error(f"Failed to remove {subdir}: {e}")
