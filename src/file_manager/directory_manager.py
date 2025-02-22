import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DirectoryManager:
    """Handles directory-related operations like ensuring existence."""

    @staticmethod
    def ensure_directory(directory: Path):
        """Ensures that a directory exists."""
        try:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured directory exists: {directory}")
        except Exception as e:
            logger.error(f"Error ensuring directory {directory}: {e}")
            raise
