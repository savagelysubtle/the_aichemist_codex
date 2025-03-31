"""Safety utilities for file operations."""

import logging
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# Default ignore patterns for file operations
DEFAULT_IGNORE_PATTERNS = [
    "__pycache__",
    ".git",
    ".vscode",
    ".idea",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".DS_Store",
    "*.so",
    "*.dylib",
    "*.dll",
    "*.bak",
    "*.swp",
    "*.tmp",
    "*.temp",
]


class SafeFileHandler:
    """Handles file operations with safety checks."""

    # Class-level ignore patterns that can be configured programmatically
    _ignore_patterns: list[str] = DEFAULT_IGNORE_PATTERNS

    @classmethod
    def configure_ignore_patterns(cls, patterns: list[str]) -> None:
        """
        Configure the ignore patterns used by should_ignore.

        Args:
            patterns: List of patterns to ignore
        """
        # Update patterns, ensuring we don't lose the defaults unless explicitly meant to
        if patterns:
            cls._ignore_patterns = DEFAULT_IGNORE_PATTERNS + [
                p for p in patterns if p not in DEFAULT_IGNORE_PATTERNS
            ]
            logger.debug(f"Updated ignore patterns: {cls._ignore_patterns}")

    @staticmethod
    def is_safe_path(base_path: Path, target_path: Path) -> bool:
        """
        Check if the target path is safe to access from the base path.

        Args:
            base_path: The base directory considered safe
            target_path: The target path to check

        Returns:
            bool: True if safe, False otherwise
        """
        try:
            # Resolve both paths to absolute with symlinks resolved
            base_abs = base_path.resolve()
            target_abs = target_path.resolve()

            # Check if the target is within the base directory
            return str(target_abs).startswith(str(base_abs))
        except Exception as e:
            logger.error(f"Error checking path safety: {e}")
            return False

    @staticmethod
    def ensure_directory(directory_path: Path) -> bool:
        """
        Ensure a directory exists, creating it if necessary.

        Args:
            directory_path: Path to the directory

        Returns:
            bool: True if directory exists or was created, False otherwise
        """
        try:
            os.makedirs(directory_path, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Error creating directory {directory_path}: {e}")
            return False

    @classmethod
    def should_ignore(cls, file_path: Path) -> bool:
        """
        Check if a file should be ignored based on configured patterns.

        Args:
            file_path: Path to the file to check

        Returns:
            bool: True if the file should be ignored, False otherwise
        """
        # Convert to string for easier pattern matching
        path_str = str(file_path)

        # Check each configured ignore pattern
        for pattern in cls._ignore_patterns:
            # Simple suffix match (for file extensions)
            if pattern.startswith("*.") and file_path.suffix == pattern[1:]:
                logger.debug(f"Ignoring {file_path} (matched pattern {pattern})")
                return True

            # Exact match for specific files or directories
            if pattern in file_path.parts:
                logger.debug(f"Ignoring {file_path} (matched directory/file {pattern})")
                return True

            # Full path contains the exact pattern
            if pattern in path_str:
                logger.debug(f"Ignoring {file_path} (matched substring {pattern})")
                return True

            # Try regex match for more complex patterns
            if pattern.startswith("^") or pattern.endswith("$"):
                try:
                    if re.search(pattern, path_str):
                        logger.debug(f"Ignoring {file_path} (matched regex {pattern})")
                        return True
                except re.error:
                    pass  # Invalid regex, ignore this pattern

        return False
