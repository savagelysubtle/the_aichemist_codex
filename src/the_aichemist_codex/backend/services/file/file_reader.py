"""
Implementation of the FileReader interface.

This module provides functionality for reading and parsing files of different formats,
using the registry pattern to avoid circular dependencies.
"""

import mimetypes

from ...core.exceptions import FileError
from ...core.interfaces import FileReader as FileReaderInterface
from ...registry import Registry


class FileReaderImpl(FileReaderInterface):
    """
    Implementation of the FileReader interface.

    This class provides functionality for reading and parsing files of different formats,
    using the registry pattern to avoid circular dependencies.
    """

    def __init__(self):
        """Initialize the FileReader instance."""
        self._registry = Registry.get_instance()
        self._paths = self._registry.project_paths
        self._validator = self._registry.file_validator
        self._async_io = self._registry.async_io

    async def read_text(self, file_path: str) -> str:
        """
        Read a text file.

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

        try:
            # Directly use AsyncIO to read the file
            return await self._async_io.read_file(file_path)
        except FileError:
            # AsyncIO already wraps errors as FileError
            raise
        except Exception as e:
            # Wrap any other errors
            raise FileError(f"Failed to read text file: {str(e)}", file_path)

    # ... [other read methods remain the same] ...

    async def get_mime_type(self, file_path: str) -> str:
        """
        Get the MIME type of a file.

        Args:
            file_path: Path to the file

        Returns:
            MIME type string

        Raises:
            FileError: If the file cannot be accessed
        """
        # Validate path safety
        self._validator.ensure_path_safe(file_path)

        try:
            # Initialize MIME types if needed
            if not mimetypes.inited:
                mimetypes.init()

            # Get MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            return mime_type or "application/octet-stream"
        except Exception as e:
            raise FileError(f"Failed to determine MIME type: {str(e)}", file_path)
