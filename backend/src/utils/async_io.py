"""Asynchronous file operations for The Aichemist Codex."""

import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Union, BinaryIO, TextIO, Any

import aiofiles

from aichemist_codex.utils.safety import SafeFileHandler

logger = logging.getLogger(__name__)


class AsyncFileIO:
    """Provides comprehensive asynchronous file I/O utilities."""

    @staticmethod
    async def read(file_path: Path) -> str:
        """Reads file content asynchronously, handling errors.

        Skips files that match the default ignore patterns using `SafeFileHandler`.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            The file content as a string, or an error message if the file can't be read
        """
        if SafeFileHandler.should_ignore(file_path):
            logger.info(f"Skipping ignored file: {file_path}")
            return f"# Skipped ignored file: {file_path}"

        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                return await f.read()
        except UnicodeDecodeError as e:
            logger.error(f"Encoding error in {file_path}: {e}")
            return f"# Encoding error: {e}"
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return f"# Error reading file: {e}"

    @staticmethod
    async def read_binary(file_path: Path) -> bytes:
        """Reads binary file content asynchronously.

        Skips files that match the default ignore patterns using `SafeFileHandler`.
        
        Args:
            file_path: Path to the binary file to read
            
        Returns:
            The file content as bytes, or empty bytes if the file can't be read
        """
        if SafeFileHandler.should_ignore(file_path):
            logger.info(f"Skipping ignored binary file: {file_path}")
            return b""

        try:
            async with aiofiles.open(file_path, "rb") as f:
                return await f.read()
        except Exception as e:
            logger.error(f"Error reading binary file {file_path}: {e}")
            return b""

    @staticmethod
    async def write(file_path: Path, content: str, encoding: str = "utf-8") -> bool:
        """Writes string content to a file asynchronously.
        
        Args:
            file_path: Path where the file should be written
            content: String content to write
            encoding: File encoding to use
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(file_path.parent, exist_ok=True)
            
            async with aiofiles.open(file_path, "w", encoding=encoding) as f:
                await f.write(content)
            return True
        except Exception as e:
            logger.error(f"Error writing to {file_path}: {e}")
            return False

    @staticmethod
    async def write_binary(file_path: Path, content: bytes) -> bool:
        """Writes binary content to a file asynchronously.
        
        Args:
            file_path: Path where the file should be written
            content: Binary content to write
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(file_path.parent, exist_ok=True)
            
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)
            return True
        except Exception as e:
            logger.error(f"Error writing binary data to {file_path}: {e}")
            return False

    @staticmethod
    async def append(file_path: Path, content: str, encoding: str = "utf-8") -> bool:
        """Appends string content to a file asynchronously.
        
        Args:
            file_path: Path where the content should be appended
            content: String content to append
            encoding: File encoding to use
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(file_path.parent, exist_ok=True)
            
            async with aiofiles.open(file_path, "a", encoding=encoding) as f:
                await f.write(content)
            return True
        except Exception as e:
            logger.error(f"Error appending to {file_path}: {e}")
            return False

    @staticmethod
    async def read_lines(file_path: Path) -> List[str]:
        """Reads file lines asynchronously.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            List of lines from the file, or empty list on error
        """
        if SafeFileHandler.should_ignore(file_path):
            logger.info(f"Skipping ignored file: {file_path}")
            return []
            
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                return await f.readlines()
        except Exception as e:
            logger.error(f"Error reading lines from {file_path}: {e}")
            return []

    @staticmethod
    async def read_json(file_path: Path) -> Dict:
        """Reads and parses JSON file asynchronously.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Parsed JSON object or empty dict on error
        """
        import json
        
        try:
            content = await AsyncFileIO.read(file_path)
            if content.startswith("#"):  # Error reading file
                return {}
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error parsing JSON from {file_path}: {e}")
            return {}

    @staticmethod
    async def write_json(file_path: Path, data: Any, indent: int = 4) -> bool:
        """Writes data as JSON to a file asynchronously.
        
        Args:
            file_path: Path where the JSON should be written
            data: Data to serialize as JSON
            indent: Number of spaces for indentation
            
        Returns:
            True if successful, False otherwise
        """
        import json
        
        try:
            json_str = json.dumps(data, indent=indent)
            return await AsyncFileIO.write(file_path, json_str)
        except Exception as e:
            logger.error(f"Error writing JSON to {file_path}: {e}")
            return False

    @staticmethod
    async def exists(file_path: Path) -> bool:
        """Checks if a file exists asynchronously.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if the file exists, False otherwise
        """
        return file_path.exists()
            
    @staticmethod
    async def copy(source: Path, destination: Path) -> bool:
        """Copies a file asynchronously.
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure destination directory exists
            os.makedirs(destination.parent, exist_ok=True)
            
            if await AsyncFileIO.exists(source):
                if source.is_file():
                    content = await AsyncFileIO.read_binary(source)
                    return await AsyncFileIO.write_binary(destination, content)
                else:
                    logger.error(f"Source {source} is not a file")
                    return False
            else:
                logger.error(f"Source file {source} does not exist")
                return False
        except Exception as e:
            logger.error(f"Error copying {source} to {destination}: {e}")
            return False


# For backward compatibility
AsyncFileReader = AsyncFileIO