"""
Implementation of the DirectoryManager class.

This module provides the core functionality for directory operations,
leveraging the new architecture to avoid circular dependencies.
"""

import os
import shutil
from pathlib import Path

from ...core.exceptions import DirectoryError
from ...core.interfaces import DirectoryManager as DirectoryManagerInterface
from ...registry import Registry


class DirectoryManager(DirectoryManagerInterface):
    """
    Directory manager class for handling directory operations.

    This class provides functionality for creating, deleting, and managing directories.
    It uses the ProjectPaths and FileValidator interfaces to avoid circular dependencies.
    """

    def __init__(self):
        """Initialize the DirectoryManager instance."""
        registry = Registry.get_instance()
        self._paths = registry.project_paths
        self._validator = registry.file_validator

        # Cache of directories that have been created
        self._created_dirs: set[Path] = set()

    async def ensure_directory_exists(self, directory_path: str) -> Path:
        """
        Ensure a directory exists, creating it if necessary.

        Args:
            directory_path: Path to the directory

        Returns:
            Path object for the directory

        Raises:
            DirectoryError: If the directory cannot be created
            UnsafePathError: If the path is unsafe
        """
        # Validate path safety
        self._validator.ensure_path_safe(directory_path)

        # Resolve the path
        path_obj = self._paths.resolve_path(directory_path)

        # Check if directory already exists in cache
        if path_obj in self._created_dirs:
            return path_obj

        # Create directory if it doesn't exist
        if not path_obj.exists():
            try:
                path_obj.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise DirectoryError(f"Failed to create directory: {path_obj}", str(e))
        elif not path_obj.is_dir():
            raise DirectoryError(f"Path exists but is not a directory: {path_obj}")

        # Add to cache of created directories
        self._created_dirs.add(path_obj)

        return path_obj

    async def list_directory(self, directory_path: str) -> list[str]:
        """
        List the contents of a directory.

        Args:
            directory_path: Path to the directory

        Returns:
            List of filenames in the directory

        Raises:
            DirectoryError: If the directory cannot be read
            UnsafePathError: If the path is unsafe
        """
        # Validate path safety
        self._validator.ensure_path_safe(directory_path)

        # Resolve the path
        path_obj = self._paths.resolve_path(directory_path)

        if not path_obj.exists():
            raise DirectoryError(f"Directory does not exist: {path_obj}")

        if not path_obj.is_dir():
            raise DirectoryError(f"Path is not a directory: {path_obj}")

        try:
            return [item.name for item in path_obj.iterdir()]
        except Exception as e:
            raise DirectoryError(f"Failed to list directory: {path_obj}", str(e))

    async def get_subdirectories(self, directory_path: str) -> list[str]:
        """
        Get a list of subdirectories in a directory.

        Args:
            directory_path: Path to the directory

        Returns:
            List of subdirectory names

        Raises:
            DirectoryError: If the directory cannot be read
            UnsafePathError: If the path is unsafe
        """
        # Validate path safety
        self._validator.ensure_path_safe(directory_path)

        # Resolve the path
        path_obj = self._paths.resolve_path(directory_path)

        if not path_obj.exists():
            raise DirectoryError(f"Directory does not exist: {path_obj}")

        if not path_obj.is_dir():
            raise DirectoryError(f"Path is not a directory: {path_obj}")

        try:
            return [item.name for item in path_obj.iterdir() if item.is_dir()]
        except Exception as e:
            raise DirectoryError(f"Failed to get subdirectories: {path_obj}", str(e))

    async def remove_directory(
        self, directory_path: str, recursive: bool = False
    ) -> bool:
        """
        Remove a directory.

        Args:
            directory_path: Path to the directory
            recursive: Whether to remove recursively

        Returns:
            True if successful, False otherwise

        Raises:
            DirectoryError: If the directory cannot be removed
            UnsafePathError: If the path is unsafe
        """
        # Validate path safety
        self._validator.ensure_path_safe(directory_path)

        # Resolve the path
        path_obj = self._paths.resolve_path(directory_path)

        if not path_obj.exists():
            return False

        if not path_obj.is_dir():
            raise DirectoryError(f"Path is not a directory: {path_obj}")

        try:
            if recursive:
                shutil.rmtree(path_obj)
            else:
                path_obj.rmdir()

            # Remove from cache if it exists
            if path_obj in self._created_dirs:
                self._created_dirs.remove(path_obj)

            return True
        except Exception as e:
            raise DirectoryError(f"Failed to remove directory: {path_obj}", str(e))

    async def is_directory_empty(self, directory_path: str) -> bool:
        """
        Check if a directory is empty.

        Args:
            directory_path: Path to the directory

        Returns:
            True if the directory is empty, False otherwise

        Raises:
            DirectoryError: If the directory cannot be read
            UnsafePathError: If the path is unsafe
        """
        # Validate path safety
        self._validator.ensure_path_safe(directory_path)

        # Resolve the path
        path_obj = self._paths.resolve_path(directory_path)

        if not path_obj.exists():
            raise DirectoryError(f"Directory does not exist: {path_obj}")

        if not path_obj.is_dir():
            raise DirectoryError(f"Path is not a directory: {path_obj}")

        try:
            return not any(path_obj.iterdir())
        except Exception as e:
            raise DirectoryError(
                f"Failed to check if directory is empty: {path_obj}", str(e)
            )

    async def copy_directory(self, source_path: str, destination_path: str) -> bool:
        """
        Copy a directory.

        Args:
            source_path: Path to the source directory
            destination_path: Path to the destination directory

        Returns:
            True if successful, False otherwise

        Raises:
            DirectoryError: If the directory cannot be copied
            UnsafePathError: If either path is unsafe
        """
        # Validate path safety
        self._validator.ensure_path_safe(source_path)
        self._validator.ensure_path_safe(destination_path)

        # Resolve the paths
        source_obj = self._paths.resolve_path(source_path)
        dest_obj = self._paths.resolve_path(destination_path)

        if not source_obj.exists():
            raise DirectoryError(f"Source directory does not exist: {source_obj}")

        if not source_obj.is_dir():
            raise DirectoryError(f"Source path is not a directory: {source_obj}")

        if dest_obj.exists() and not dest_obj.is_dir():
            raise DirectoryError(
                f"Destination path exists but is not a directory: {dest_obj}"
            )

        try:
            if dest_obj.exists():
                # If destination exists, copy contents
                for item in source_obj.glob("*"):
                    if item.is_dir():
                        shutil.copytree(item, dest_obj / item.name, dirs_exist_ok=True)
                    else:
                        shutil.copy2(item, dest_obj / item.name)
            else:
                # If destination doesn't exist, copy the entire directory
                shutil.copytree(source_obj, dest_obj)

            # Add destination to cache
            self._created_dirs.add(dest_obj)

            return True
        except Exception as e:
            raise DirectoryError(
                f"Failed to copy directory from {source_obj} to {dest_obj}", str(e)
            )

    async def get_directory_size(self, directory_path: str) -> int:
        """
        Get the total size of a directory in bytes.

        Args:
            directory_path: Path to the directory

        Returns:
            Size of the directory in bytes

        Raises:
            DirectoryError: If the directory size cannot be calculated
            UnsafePathError: If the path is unsafe
        """
        # Validate path safety
        self._validator.ensure_path_safe(directory_path)

        # Resolve the path
        path_obj = self._paths.resolve_path(directory_path)

        if not path_obj.exists():
            raise DirectoryError(f"Directory does not exist: {path_obj}")

        if not path_obj.is_dir():
            raise DirectoryError(f"Path is not a directory: {path_obj}")

        try:
            total_size = 0
            for dirpath, _, filenames in os.walk(path_obj):
                for filename in filenames:
                    file_path = Path(dirpath) / filename
                    total_size += file_path.stat().st_size

            return total_size
        except Exception as e:
            raise DirectoryError(
                f"Failed to calculate directory size: {path_obj}", str(e)
            )
