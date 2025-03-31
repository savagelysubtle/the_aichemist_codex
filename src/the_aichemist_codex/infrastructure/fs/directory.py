import asyncio
import logging
import os
from pathlib import Path

from the_aichemist_codex.infrastructure.fs.rollback import (
    OperationType,
    RollbackManager,
)

logger = logging.getLogger(__name__)
rollback_manager = RollbackManager()


class DirectoryManager:
    """
    Central manager for data directory access.

    This class provides standardized access to project data directories,
    handling creation, validation, and path resolution.
    """

    # Standard directory types
    STANDARD_DIRS = ["cache", "logs", "versions", "exports", "backup", "trash"]

    def __init__(self, base_dir: Path | None = None) -> None:
        """
        Initialize with optional base directory override.

        Args:
            base_dir: Optional custom base directory path
        """
        self.base_dir = base_dir or self._get_default_data_dir()
        self._ensure_directories_exist()

    def _get_default_data_dir(self) -> Path:
        """
        Get the default data directory based on env vars or system location.

        Returns:
            Path: The resolved data directory path
        """
        # Check for environment variable override
        if env_dir := os.environ.get("AICHEMIST_DATA_DIR"):
            return Path(env_dir)

        # Use standard OS-specific data directories
        if os.name == "nt":  # Windows
            return Path(os.environ["APPDATA"]) / "AichemistCodex"
        else:  # Linux/Mac
            return Path.home() / ".aichemist"

    def _ensure_directories_exist(self) -> None:
        """Create all required directories if they don't exist."""
        for subdir in self.STANDARD_DIRS:
            (self.base_dir / subdir).mkdir(parents=True, exist_ok=True)

    def get_dir(self, dir_type: str) -> Path:
        """
        Get a specific subdirectory path.

        Args:
            dir_type: Directory type (cache, logs, versions, etc.)

        Returns:
            Path: The resolved directory path

        Raises:
            ValueError: If the directory type is not recognized
        """
        if dir_type not in self.STANDARD_DIRS:
            raise ValueError(f"Unknown directory type: {dir_type}")
        return self.base_dir / dir_type

    def get_file_path(self, filename: str) -> Path:
        """
        Get path for a file in the base data directory.

        Args:
            filename: Name of the file

        Returns:
            Path: The resolved file path
        """
        return self.base_dir / filename

    async def ensure_directory(self, directory: Path) -> None:
        """
        Ensures that a directory exists asynchronously and records a rollback for creation.

        Args:
            directory: The directory path to ensure exists
        """
        directory = directory.resolve()

        # Use async existence check
        dir_exists = await asyncio.to_thread(directory.exists)

        if not dir_exists:
            try:
                await asyncio.to_thread(directory.mkdir, parents=True, exist_ok=True)
                logger.info(f"Ensured directory exists: {directory}")
                # Record the creation so that an undo would delete this new directory
                rollback_manager.record_operation(OperationType.CREATE, directory)
            except Exception as e:
                logger.error(f"Error ensuring directory {directory}: {e}")
        else:
            logger.debug(f"Directory already exists: {directory}")

    async def cleanup_empty_dirs(self, directory: Path) -> None:
        """
        Recursively removes empty directories asynchronously and records a rollback for each deletion.

        Args:
            directory: The base directory to clean up
        """
        directory = directory.resolve()

        async def remove_if_empty(subdir: Path) -> None:
            # Check if directory exists and is empty
            is_dir = await asyncio.to_thread(subdir.is_dir)
            if not is_dir:
                return

            # Check if directory is empty (convert to list to properly evaluate)
            dir_contents = await asyncio.to_thread(lambda: list(subdir.iterdir()))
            if not dir_contents:
                try:
                    # Record deletion before removing the directory
                    rollback_manager.record_operation(OperationType.DELETE, subdir)
                    await asyncio.to_thread(subdir.rmdir)
                    logger.info(f"Removed empty directory: {subdir}")
                except Exception as e:
                    logger.error(f"Failed to remove {subdir}: {e}")

        # Get all subdirectories
        subdirs = await asyncio.to_thread(lambda: list(directory.glob("**/")))

        # Process each subdirectory
        for subdir in sorted(subdirs, reverse=True):  # Process deeper directories first
            await remove_if_empty(subdir)
