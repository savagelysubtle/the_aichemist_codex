"""
Implementation of the FileWriter interface.

This module provides functionality for writing data to files in different formats,
using the registry pattern to avoid circular dependencies.
"""

import json
import os
from typing import Any

import yaml

from ...core.exceptions import FileError
from ...core.interfaces import FileWriter as FileWriterInterface
from ...registry import Registry


class FileWriterImpl(FileWriterInterface):
    """
    Implementation of the FileWriter interface.

    This class provides functionality for writing data to files in different formats,
    using the registry pattern to avoid circular dependencies.
    """

    def __init__(self):
        """Initialize the FileWriter instance."""
        self._registry = Registry.get_instance()
        self._paths = self._registry.project_paths
        self._validator = self._registry.file_validator
        self._async_io = self._registry.async_io

    async def write_text(self, file_path: str, content: str) -> None:
        """
        Write text to a file.

        Args:
            file_path: Path to the file
            content: Text content to write

        Raises:
            FileError: If the file cannot be written
            UnsafePathError: If the path is unsafe
        """
        # Validate path safety
        self._validator.ensure_path_safe(file_path)

        try:
            # Use AsyncIO to write the file
            await self._async_io.write_file(file_path, content)
        except FileError:
            # AsyncIO already wraps errors as FileError
            raise
        except Exception as e:
            # Wrap any other errors
            raise FileError(f"Failed to write text file: {str(e)}", file_path)

    async def write_binary(self, file_path: str, content: bytes) -> None:
        """
        Write binary data to a file.

        Args:
            file_path: Path to the file
            content: Binary content to write

        Raises:
            FileError: If the file cannot be written
            UnsafePathError: If the path is unsafe
        """
        # Validate path safety
        self._validator.ensure_path_safe(file_path)

        # Ensure the directory exists
        directory = os.path.dirname(file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        try:
            # Resolve the path
            path_obj = self._paths.resolve_path(file_path)

            # Write the binary data
            with open(path_obj, "wb") as f:
                f.write(content)
        except Exception as e:
            raise FileError(f"Failed to write binary file: {str(e)}", file_path)

    async def write_json(self, file_path: str, data: Any) -> None:
        """
        Write data as JSON to a file.

        Args:
            file_path: Path to the file
            data: Data to serialize as JSON

        Raises:
            FileError: If the data cannot be serialized or the file cannot be written
            UnsafePathError: If the path is unsafe
        """
        try:
            # Serialize the data to JSON
            try:
                json_content = json.dumps(data, indent=4, sort_keys=True, default=str)
            except Exception as e:
                raise FileError(
                    f"Failed to serialize data to JSON: {str(e)}", file_path
                )

            # Write the JSON content
            await self.write_text(file_path, json_content)
        except FileError:
            # Pass through FileError exceptions
            raise
        except Exception as e:
            # Wrap any other errors
            raise FileError(f"Failed to write JSON file: {str(e)}", file_path)

    async def write_yaml(self, file_path: str, data: Any) -> None:
        """
        Write data as YAML to a file.

        Args:
            file_path: Path to the file
            data: Data to serialize as YAML

        Raises:
            FileError: If the data cannot be serialized or the file cannot be written
            UnsafePathError: If the path is unsafe
        """
        try:
            # Serialize the data to YAML
            try:
                yaml_content = yaml.dump(
                    data, default_flow_style=False, sort_keys=False
                )
            except Exception as e:
                raise FileError(
                    f"Failed to serialize data to YAML: {str(e)}", file_path
                )

            # Write the YAML content
            await self.write_text(file_path, yaml_content)
        except FileError:
            # Pass through FileError exceptions
            raise
        except Exception as e:
            # Wrap any other errors
            raise FileError(f"Failed to write YAML file: {str(e)}", file_path)

    async def append_text(self, file_path: str, content: str) -> None:
        """
        Append text to a file.

        Args:
            file_path: Path to the file
            content: Text content to append

        Raises:
            FileError: If the file cannot be written
            UnsafePathError: If the path is unsafe
        """
        # Validate path safety
        self._validator.ensure_path_safe(file_path)

        # Resolve the path
        path_obj = self._paths.resolve_path(file_path)

        try:
            # Ensure the directory exists
            directory = os.path.dirname(str(path_obj))
            if directory:
                os.makedirs(directory, exist_ok=True)

            # Append to the file
            with open(path_obj, "a", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            raise FileError(f"Failed to append to file: {str(e)}", file_path)
