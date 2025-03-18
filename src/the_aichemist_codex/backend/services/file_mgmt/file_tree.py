"""
Implementation of the FileTree interface.

This module provides functionality for working with the file tree structure,
using the registry pattern to avoid circular dependencies.
"""

import fnmatch
from pathlib import Path
from typing import Any

from ...core.exceptions import DirectoryError
from ...core.interfaces import FileTree as FileTreeInterface
from ...registry import Registry


class FileTreeImpl(FileTreeInterface):
    """
    Implementation of the FileTree interface.

    This class provides functionality for working with file tree structures,
    using the registry pattern to avoid circular dependencies.
    """

    def __init__(self):
        """Initialize the FileTree instance."""
        self._registry = Registry.get_instance()
        self._paths = self._registry.project_paths
        self._validator = self._registry.file_validator

        # Set of directories to exclude from tree operations
        self._excluded_dirs: set[str] = {
            ".git",
            "__pycache__",
            ".vscode",
            ".idea",
            "node_modules",
        }

    async def get_tree(self, root_dir: str, max_depth: int = None) -> dict:
        """
        Get a file tree structure starting from a root directory.

        Args:
            root_dir: The root directory
            max_depth: Maximum depth to traverse

        Returns:
            Dictionary representing the file tree

        Raises:
            DirectoryError: If the directory cannot be read
            UnsafePathError: If the path is unsafe
        """
        # Validate path safety
        self._validator.ensure_path_safe(root_dir)

        # Resolve the path
        path_obj = self._paths.resolve_path(root_dir)

        if not path_obj.exists():
            raise DirectoryError(f"Directory does not exist: {path_obj}")

        if not path_obj.is_dir():
            raise DirectoryError(f"Path is not a directory: {path_obj}")

        # Build the tree recursively
        return await self._build_tree(path_obj, max_depth, current_depth=0)

    async def find_files(
        self, root_dir: str, pattern: str, max_depth: int = None
    ) -> list[str]:
        """
        Find files matching a pattern in a directory tree.

        Args:
            root_dir: The root directory
            pattern: Glob pattern to match files
            max_depth: Maximum depth to traverse

        Returns:
            List of matching file paths

        Raises:
            DirectoryError: If the directory cannot be read
            UnsafePathError: If the path is unsafe
        """
        # Validate path safety
        self._validator.ensure_path_safe(root_dir)

        # Resolve the path
        path_obj = self._paths.resolve_path(root_dir)

        if not path_obj.exists():
            raise DirectoryError(f"Directory does not exist: {path_obj}")

        if not path_obj.is_dir():
            raise DirectoryError(f"Path is not a directory: {path_obj}")

        # Find files matching the pattern
        matching_files = await self._find_files_recursive(
            path_obj, pattern, max_depth, current_depth=0
        )

        # Convert paths to strings
        return [str(path) for path in matching_files]

    async def _build_tree(
        self, directory: Path, max_depth: int | None, current_depth: int
    ) -> dict[str, Any]:
        """
        Build a tree structure recursively.

        Args:
            directory: The directory to build the tree for
            max_depth: Maximum depth to traverse
            current_depth: Current depth in the tree

        Returns:
            Dictionary representing the directory tree
        """
        # Check if we've reached the maximum depth
        if max_depth is not None and current_depth > max_depth:
            return {
                "name": directory.name,
                "path": str(directory),
                "type": "directory",
                "truncated": True,
                "children": [],
            }

        # Get the contents of the directory
        try:
            contents = list(directory.iterdir())
        except Exception as e:
            raise DirectoryError(f"Failed to read directory: {directory}", str(e))

        # Prepare the result
        result = {
            "name": directory.name,
            "path": str(directory),
            "type": "directory",
            "children": [],
        }

        # Process files first
        files = sorted(
            [item for item in contents if item.is_file()], key=lambda x: x.name
        )
        for file_path in files:
            try:
                # Basic file information
                file_info = {
                    "name": file_path.name,
                    "path": str(file_path),
                    "type": "file",
                    "extension": file_path.suffix.lower()[1:]
                    if file_path.suffix
                    else "",
                    "size": file_path.stat().st_size,
                }
                result["children"].append(file_info)
            except Exception:
                # Skip files with errors
                continue

        # Then process directories
        directories = sorted(
            [item for item in contents if item.is_dir()], key=lambda x: x.name
        )
        for dir_path in directories:
            # Skip excluded directories
            if dir_path.name in self._excluded_dirs:
                continue

            try:
                # Recursively build tree for subdirectories
                dir_tree = await self._build_tree(
                    dir_path, max_depth, current_depth + 1
                )
                result["children"].append(dir_tree)
            except Exception:
                # Skip directories with errors
                continue

        return result

    async def _find_files_recursive(
        self, directory: Path, pattern: str, max_depth: int | None, current_depth: int
    ) -> list[Path]:
        """
        Find files matching a pattern recursively.

        Args:
            directory: The directory to search in
            pattern: Glob pattern to match files
            max_depth: Maximum depth to traverse
            current_depth: Current depth in the tree

        Returns:
            List of matching file paths
        """
        # Check if we've reached the maximum depth
        if max_depth is not None and current_depth > max_depth:
            return []

        # Get the contents of the directory
        try:
            contents = list(directory.iterdir())
        except Exception as e:
            raise DirectoryError(f"Failed to read directory: {directory}", str(e))

        matching_files = []

        # Process files
        files = [item for item in contents if item.is_file()]
        for file_path in files:
            if fnmatch.fnmatch(file_path.name, pattern):
                matching_files.append(file_path)

        # Process directories
        directories = [item for item in contents if item.is_dir()]
        for dir_path in directories:
            # Skip excluded directories
            if dir_path.name in self._excluded_dirs:
                continue

            # Recursively search subdirectories
            try:
                subdir_matches = await self._find_files_recursive(
                    dir_path, pattern, max_depth, current_depth + 1
                )
                matching_files.extend(subdir_matches)
            except Exception:
                # Skip directories with errors
                continue

        return matching_files
