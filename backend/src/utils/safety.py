"""Ensures file operations remain within safe directories and ignore patterns."""

import logging
from pathlib import Path

from src.config.settings import DEFAULT_IGNORE_PATTERNS

logger = logging.getLogger(__name__)


class SafeFileHandler:
    """Provides validation utilities to ensure safe file operations."""

    @staticmethod
    def is_safe_path(target: Path, base: Path) -> bool:
        """Ensures that a target path is within the base directory."""
        try:
            return base.resolve() in target.resolve().parents
        except (FileNotFoundError, RuntimeError):
            return False

    @staticmethod
    def should_ignore(file_path: Path) -> bool:
        """Checks if a file should be ignored based on default ignore patterns."""
        for pattern in DEFAULT_IGNORE_PATTERNS:
            if file_path.match(pattern):
                logger.info(f"Skipping ignored file: {file_path} (matched {pattern})")
                return True
            if any(part == pattern for part in file_path.parts):  # Check parent directories
                logger.info(f"Skipping ignored directory: {file_path} (matched {pattern})")
                return True
        return False

    @staticmethod
    def is_binary_file(file_path: Path) -> bool:
        """Determines if a file is binary by checking its extension."""
        binary_extensions = {
            ".png",
            ".jpg",
            ".jpeg",
            ".exe",
            ".dll",
            ".zip",
            ".tar",
            ".gz",
        }
        return file_path.suffix in binary_extensions
