"""
Implementation of the FileReader interface.

This module provides functionality for reading and parsing files of different formats,
using the registry pattern to avoid circular dependencies.
"""

import json
import logging
import mimetypes
import os
from pathlib import Path
from typing import Any, Dict

import yaml

from ...core.exceptions import FileError, FileReaderError
from ...core.interfaces import FileReader as FileReaderInterface
from ...core.models import FileMetadata
from ...registry import Registry
from .parsers import get_parser_for_mime_type

logger = logging.getLogger(__name__)

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
        self._preview_length = 100  # Default preview length

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

    async def read_binary(self, file_path: str) -> bytes:
        """
        Read a binary file.

        Args:
            file_path: Path to the file

        Returns:
            The file contents as bytes

        Raises:
            FileError: If the file cannot be read
            UnsafePathError: If the path is unsafe
        """
        # Validate path safety
        self._validator.ensure_path_safe(file_path)

        # Resolve the path
        path_obj = self._paths.resolve_path(file_path)

        if not path_obj.exists():
            raise FileError(f"File does not exist: {file_path}", file_path)

        try:
            # Read file as binary
            with open(path_obj, "rb") as f:
                return f.read()
        except Exception as e:
            raise FileError(f"Failed to read binary file: {str(e)}", file_path)

    async def read_json(self, file_path: str) -> Any:
        """
        Read and parse a JSON file.

        Args:
            file_path: Path to the file

        Returns:
            The parsed JSON data

        Raises:
            FileError: If the file cannot be read or parsed
            UnsafePathError: If the path is unsafe
        """
        try:
            # First read the file as text
            content = await self.read_text(file_path)

            # Parse the JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                raise FileError(f"Failed to parse JSON: {str(e)}", file_path)

        except FileError:
            # Pass through FileError exceptions
            raise
        except Exception as e:
            # Wrap any other errors
            raise FileError(f"Failed to read JSON file: {str(e)}", file_path)

    async def read_yaml(self, file_path: str) -> Any:
        """
        Read and parse a YAML file.

        Args:
            file_path: Path to the file

        Returns:
            The parsed YAML data

        Raises:
            FileError: If the file cannot be read or parsed
            UnsafePathError: If the path is unsafe
        """
        try:
            # First read the file as text
            content = await self.read_text(file_path)

            # Parse the YAML
            try:
                return yaml.safe_load(content)
            except yaml.YAMLError as e:
                raise FileError(f"Failed to parse YAML: {str(e)}", file_path)

        except FileError:
            # Pass through FileError exceptions
            raise
        except Exception as e:
            # Wrap any other errors
            raise FileError(f"Failed to read YAML file: {str(e)}", file_path)

    async def read_lines(self, file_path: str) -> list[str]:
        """
        Read a file and return its contents as a list of lines.

        Args:
            file_path: Path to the file

        Returns:
            List of lines in the file

        Raises:
            FileError: If the file cannot be read
            UnsafePathError: If the path is unsafe
        """
        try:
            content = await self.read_text(file_path)
            return content.splitlines()
        except FileError:
            # Pass through FileError exceptions
            raise
        except Exception as e:
            # Wrap any other errors
            raise FileError(f"Failed to read file lines: {str(e)}", file_path)

    async def read_config(self, file_path: str) -> dict[str, Any]:
        """
        Read a configuration file (JSON or YAML) based on extension.

        Args:
            file_path: Path to the file

        Returns:
            The parsed configuration data

        Raises:
            FileError: If the file cannot be read or parsed
            UnsafePathError: If the path is unsafe
        """
        # Get the file extension
        path_obj = Path(file_path)
        extension = path_obj.suffix.lower()

        if extension in (".yaml", ".yml"):
            return await self.read_yaml(file_path)
        elif extension == ".json":
            return await self.read_json(file_path)
        else:
            raise FileError(
                f"Unsupported configuration file format: {extension}", file_path
            )

    def get_mime_type(self, file_path: str) -> str:
        """Get the MIME type of a file.

        Args:
            file_path: Path to the file

        Returns:
            MIME type of the file
        """
        try:
            import mimetypes
            mime_type, _ = mimetypes.guess_type(file_path)
            return mime_type or "application/octet-stream"
        except Exception as e:
            logger.warning(f"Error determining MIME type for {file_path}: {str(e)}")
            return "application/octet-stream"

    async def process_file(self, file_path: str) -> FileMetadata:
        """
        Process a file to extract metadata and content preview.

        Args:
            file_path: Path to the file

        Returns:
            FileMetadata object with file information

        Raises:
            FileError: If the file cannot be processed
        """
        # Implementation details...

    def extract_metadata(self, file_path: str) -> dict[str, Any]:
        """Extract metadata from a file using the metadata manager.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary containing metadata

        Raises:
            FileReaderError: If metadata extraction fails
        """
        try:
            mime_type = self.get_mime_type(file_path)

            # Try to get metadata manager from registry
            try:
                metadata_manager = self._registry.metadata_manager
                return metadata_manager.extract_metadata(file_path, mime_type)
            except AttributeError:
                # Metadata manager not available in registry
                logger.warning("Metadata manager not available in registry")

                # Fall back to basic file stats
                stat_info = os.stat(file_path)
                return {
                    "file_path": file_path,
                    "file_name": os.path.basename(file_path),
                    "extension": os.path.splitext(file_path)[1].lower(),
                    "mime_type": mime_type,
                    "size_bytes": stat_info.st_size,
                    "last_modified": stat_info.st_mtime,
                    "created": stat_info.st_ctime
                }
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {str(e)}")
            raise FileReaderError(f"Failed to extract metadata from {file_path}: {str(e)}") from e

    def generate_preview(self, file_path: str, max_size: int = 1000) -> str:
        """Generate a preview of a file using the metadata manager.

        Args:
            file_path: Path to the file
            max_size: Maximum size of the preview in characters

        Returns:
            Preview of the file content

        Raises:
            FileReaderError: If preview generation fails
        """
        try:
            mime_type = self.get_mime_type(file_path)

            # Try to get metadata manager from registry
            try:
                metadata_manager = self._registry.metadata_manager
                return metadata_manager.generate_preview(file_path, max_size, mime_type)
            except AttributeError:
                # Metadata manager not available in registry
                logger.warning("Metadata manager not available in registry")

                # Fall back to basic preview based on file type
                _, ext = os.path.splitext(file_path)
                ext = ext.lower()

                if ext in {".txt", ".md", ".csv", ".json", ".yaml", ".yml", ".xml", ".html"}:
                    # Text files: read directly
                    try:
                        with open(file_path, encoding='utf-8') as f:
                            content = f.read(max_size + 1)
                            if len(content) > max_size:
                                return content[:max_size] + "..."
                            return content
                    except UnicodeDecodeError:
                        return f"[Binary file: {os.path.basename(file_path)}]"
                else:
                    # Binary or unsupported files
                    return f"[File: {os.path.basename(file_path)}]"
        except Exception as e:
            logger.error(f"Error generating preview for {file_path}: {str(e)}")
            raise FileReaderError(f"Failed to generate preview for {file_path}: {str(e)}") from e
