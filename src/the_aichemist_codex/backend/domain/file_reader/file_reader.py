"""
Implementation of the FileReader interface.

This module provides functionality for reading and parsing files of different formats,
using the registry pattern to avoid circular dependencies.
"""

import json
from pathlib import Path
from typing import Any

import yaml

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
