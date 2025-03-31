"""
File System Operations Module - Provides functions for file operations.
"""

import logging
import os
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any


class FileOperationError(Exception):
    """Exception raised for errors in file operations."""

    pass


class FileOperations:
    """Class for performing file system operations with logging and error handling."""

    def __init__(self, backup_enabled: bool = True, backup_dir: str | None = None):
        """
        Initialize FileOperations.

        Args:
            backup_enabled: Whether to create backups before operations
            backup_dir: Directory for storing backups (default is .aichemist_backups)
        """
        self.logger = logging.getLogger(__name__)
        self.backup_enabled = backup_enabled

        if backup_enabled:
            if backup_dir:
                self.backup_dir = Path(backup_dir)
            else:
                self.backup_dir = Path.home() / ".aichemist_backups"

            # Create backup directory if it doesn't exist
            self.backup_dir.mkdir(parents=True, exist_ok=True)

    def _backup_file(self, file_path: Path) -> Path | None:
        """Create a backup of a file before modifying it."""
        if not self.backup_enabled or not file_path.exists():
            return None

        try:
            # Create a unique backup filename
            backup_path = self.backup_dir / f"{file_path.name}.bak"

            # Make the backup
            shutil.copy2(file_path, backup_path)
            self.logger.debug(f"Created backup of {file_path} at {backup_path}")

            return backup_path
        except Exception as e:
            self.logger.warning(f"Failed to create backup of {file_path}: {e}")
            return None

    def create_directory(self, directory_path: str | Path) -> Path:
        """
        Create a directory if it doesn't exist.

        Args:
            directory_path: Path to the directory

        Returns:
            Path object for the created directory
        """
        path = Path(directory_path)

        try:
            path.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created directory: {path}")
            return path
        except Exception as e:
            self.logger.error(f"Failed to create directory {path}: {e}")
            raise FileOperationError(f"Failed to create directory: {e}")

    def copy_file(
        self, source: str | Path, destination: str | Path, overwrite: bool = False
    ) -> Path:
        """
        Copy a file from source to destination.

        Args:
            source: Source file path
            destination: Destination file path
            overwrite: Whether to overwrite existing files

        Returns:
            Path object for the destination file
        """
        src_path = Path(source)
        dest_path = Path(destination)

        if not src_path.exists():
            raise FileOperationError(f"Source file does not exist: {src_path}")

        if dest_path.exists() and not overwrite:
            raise FileOperationError(f"Destination file already exists: {dest_path}")

        try:
            # Create parent directories if they don't exist
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy the file
            shutil.copy2(src_path, dest_path)
            self.logger.info(f"Copied {src_path} to {dest_path}")

            return dest_path
        except Exception as e:
            self.logger.error(f"Failed to copy {src_path} to {dest_path}: {e}")
            raise FileOperationError(f"Failed to copy file: {e}")

    def move_file(
        self, source: str | Path, destination: str | Path, overwrite: bool = False
    ) -> Path:
        """
        Move a file from source to destination.

        Args:
            source: Source file path
            destination: Destination file path
            overwrite: Whether to overwrite existing files

        Returns:
            Path object for the destination file
        """
        src_path = Path(source)
        dest_path = Path(destination)

        if not src_path.exists():
            raise FileOperationError(f"Source file does not exist: {src_path}")

        if dest_path.exists() and not overwrite:
            raise FileOperationError(f"Destination file already exists: {dest_path}")

        try:
            # Create a backup of the source file
            backup_path = self._backup_file(src_path)

            # Create parent directories if they don't exist
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Move the file
            shutil.move(src_path, dest_path)
            self.logger.info(f"Moved {src_path} to {dest_path}")

            return dest_path
        except Exception as e:
            self.logger.error(f"Failed to move {src_path} to {dest_path}: {e}")
            raise FileOperationError(f"Failed to move file: {e}")

    def delete_file(self, file_path: str | Path, secure: bool = False) -> bool:
        """
        Delete a file.

        Args:
            file_path: Path to the file
            secure: Whether to perform secure deletion (overwrite with zeros)

        Returns:
            True if deletion was successful
        """
        path = Path(file_path)

        if not path.exists():
            self.logger.warning(f"File does not exist: {path}")
            return False

        try:
            # Create a backup before deletion
            backup_path = self._backup_file(path)

            if secure and path.is_file():
                # Perform secure deletion by overwriting with zeros
                file_size = path.stat().st_size
                with open(path, "wb") as f:
                    f.write(b"\x00" * file_size)
                    f.flush()
                    os.fsync(f.fileno())

            # Delete the file
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)

            self.logger.info(f"Deleted {'(secure) ' if secure else ''}{path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete {path}: {e}")
            raise FileOperationError(f"Failed to delete file: {e}")

    def batch_operation(
        self, operation: Callable, items: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Perform a batch operation on multiple files.

        Args:
            operation: Function to call for each item
            items: List of parameter dictionaries for each operation

        Returns:
            List of results (success/failure) for each operation
        """
        results = []

        for item in items:
            try:
                result = operation(**item)
                results.append({"success": True, "params": item, "result": result})
            except Exception as e:
                self.logger.error(f"Batch operation failed for {item}: {e}")
                results.append({"success": False, "params": item, "error": str(e)})

        return results
