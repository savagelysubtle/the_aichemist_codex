"""Asynchronous file operations for The Aichemist Codex."""

import logging
from pathlib import Path

import aiofiles

from aichemist_codex.utils.safety import (
    SafeFileHandler,
)  # ✅ Use centralized file handling

logger = logging.getLogger(__name__)


class AsyncFileReader:
    """Provides asynchronous file reading utilities."""

    @staticmethod
    async def read(file_path: Path) -> str:
        """Reads file content asynchronously, handling errors.

        Skips files that match the default ignore patterns using `SafeFileHandler`.
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
