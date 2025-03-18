"""
Implementation of the AsyncIO interface.

This module provides concrete implementation for asynchronous file I/O operations,
addressing circular dependencies with safety and other modules.
"""

import os
from pathlib import Path

import aiofiles

from ...core.constants import DEFAULT_ENCODING, MAX_FILE_SIZE_MB
from ...core.exceptions import FileError
from ...core.interfaces import AsyncIO
from ...registry import Registry


class AsyncIOImpl(AsyncIO):
    """Concrete implementation of the AsyncIO interface."""

    def __init__(self):
        """Initialize the AsyncIO instance."""
        self._validator = Registry.get_instance().file_validator

    async def read_file(self, file_path: str) -> str:
        """
        Read a file asynchronously.

        Args:
            file_path: Path to the file

        Returns:
            The file contents as a string

        Raises:
            FileError: If the file cannot be read
            UnsafePathError: If the path is unsafe
        """
        # Validate path safety
        self._validator.ensure_path_safe(file_path)

        # Check if file exists
        path_obj = Path(file_path)
        if not path_obj.exists():
            raise FileError(f"File does not exist: {file_path}", file_path)

        # Check if file size is within limits
        file_size_mb = path_obj.stat().st_size / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            raise FileError(
                f"File is too large: {file_size_mb:.2f} MB (max {MAX_FILE_SIZE_MB} MB)",
                file_path,
            )

        try:
            # Read file
            async with aiofiles.open(file_path, encoding=DEFAULT_ENCODING) as file:
                return await file.read()
        except UnicodeDecodeError:
            # Try reading as binary and then convert to string
            try:
                async with aiofiles.open(file_path, mode="rb") as file:
                    binary_content = await file.read()
                return binary_content.decode(DEFAULT_ENCODING, errors="replace")
            except Exception as e:
                raise FileError(f"Failed to read file as binary: {str(e)}", file_path)
        except Exception as e:
            raise FileError(f"Failed to read file: {str(e)}", file_path)

    async def write_file(self, file_path: str, content: str) -> None:
        """
        Write to a file asynchronously.

        Args:
            file_path: Path to the file
            content: Content to write

        Raises:
            FileError: If the file cannot be written
            UnsafePathError: If the path is unsafe
        """
        # Validate path safety
        self._validator.ensure_path_safe(file_path)

        # Ensure directory exists
        path_obj = Path(file_path)
        os.makedirs(path_obj.parent, exist_ok=True)

        try:
            # Write file
            async with aiofiles.open(
                file_path, mode="w", encoding=DEFAULT_ENCODING
            ) as file:
                await file.write(content)
        except Exception as e:
            raise FileError(f"Failed to write file: {str(e)}", file_path)

    async def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists asynchronously.

        Args:
            file_path: Path to the file

        Returns:
            True if the file exists, False otherwise

        Raises:
            UnsafePathError: If the path is unsafe
        """
        # Validate path safety
        self._validator.ensure_path_safe(file_path)

        # Check if file exists
        return Path(file_path).exists()
