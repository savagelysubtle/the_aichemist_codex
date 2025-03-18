"""
File Manager implementation for The Aichemist Codex.

This module provides functionality for file operations such as moving, copying,
detecting changes, versioning, and monitoring directories for changes.
"""

import logging
import shutil
from pathlib import Path
from typing import Any

from ...core.exceptions import FileError, FileManagerError
from ...core.interfaces import FileManager as FileManagerInterface
from ...registry import Registry

logger = logging.getLogger(__name__)


class FileManagerImpl(FileManagerInterface):
    """Implementation of the FileManager interface."""

    def __init__(self):
        """Initialize the FileManager implementation."""
        self._registry = Registry.get_instance()
        self._file_reader = self._registry.file_reader
        self._file_writer = self._registry.file_writer
        self._directory_manager = self._registry.directory_manager
        self._project_paths = self._registry.project_paths

        # For monitoring directories
        self._monitors: dict[str, dict[str, Any]] = {}
        self._monitor_id_counter = 0
        self._is_initialized = False

    async def initialize(self) -> None:
        """Initialize the file manager."""
        if self._is_initialized:
            return

        logger.info("Initializing FileManager")
        # Create any required directories
        versions_dir = self._project_paths.get_data_dir() / "versions"
        await self._directory_manager.ensure_directory_exists(str(versions_dir))

        self._is_initialized = True
        logger.info("FileManager initialized successfully")

    async def close(self) -> None:
        """Close the file manager and release resources."""
        logger.info("Closing FileManager")

        # Stop all active directory monitors
        for monitor_id in list(self._monitors.keys()):
            await self.stop_monitoring(monitor_id)

        self._is_initialized = False
        logger.info("FileManager closed successfully")

    # Implement required methods as defined in the interface
    # (move_file, copy_file, create_version, restore_version, etc.)

    async def move_file(
        self, source_path: Path, destination_path: Path, create_dirs: bool = True
    ) -> Path:
        """
        Move a file from source_path to destination_path.

        Args:
            source_path: Path to the source file
            destination_path: Path to move the file to
            create_dirs: Whether to create parent directories if needed

        Returns:
            The path to the moved file

        Raises:
            FileManagerError: If moving the file fails
        """
        self._ensure_initialized()

        try:
            # Ensure source exists
            if not source_path.exists():
                raise FileError(f"Source file does not exist: {source_path}")

            # Create parent directories if needed
            if create_dirs:
                await self._directory_manager.ensure_directory_exists(
                    str(destination_path.parent)
                )

            # Move the file
            shutil.move(str(source_path), str(destination_path))

            logger.info(f"Moved file from {source_path} to {destination_path}")
            return destination_path

        except FileError:
            # Re-raise FileError as is
            raise
        except Exception as e:
            # Wrap other exceptions
            raise FileManagerError(
                f"Failed to move file: {e}",
                file_path=str(source_path),
                operation="move_file",
            ) from e

    # Implement additional methods as needed
    # (detect_changes, monitor_directory, etc.)

    def _ensure_initialized(self) -> None:
        """Ensure the file manager is initialized."""
        if not self._is_initialized:
            raise FileManagerError("FileManager is not initialized")
