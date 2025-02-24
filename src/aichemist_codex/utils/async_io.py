"""Asynchronous file operations for The Aichemist Codex."""

import logging
from pathlib import Path

import aiofiles

logger = logging.getLogger(__name__)


class AsyncFileReader:
    """Provides asynchronous file reading utilities."""

    @staticmethod
    async def read(file_path: Path) -> str:
        """Reads file content asynchronously, handling errors."""
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
        """Reads binary file content asynchronously."""
        try:
            async with aiofiles.open(file_path, "rb") as f:
                return await f.read()
        except Exception as e:
            logger.error(f"Error reading binary file {file_path}: {e}")
            return b""
