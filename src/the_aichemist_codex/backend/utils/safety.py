"""Ensures file operations remain within safe directories and ignore patterns."""

import logging
from pathlib import Path

from the_aichemist_codex.backend.config.config_loader import config

logger = logging.getLogger(__name__)


class SafeFileHandler:
    """Provides validation utilities to ensure safe file operations."""

    @staticmethod
    def is_safe_path(target: Path, base: Path) -> bool:
        """Ensures that a target path is within the base directory."""
        try:
            return base.resolve() in target.resolve().parents
        except (FileNotFoundError, RuntimeError):
            # If there's an error resolving paths, consider it unsafe
            return False

    @staticmethod
    def should_ignore(file_path: Path) -> bool:
        """
        Checks if a file should be ignored based on default and user-configured ignore patterns.

        Uses both the default ignore patterns and any additional patterns
        specified in the config file.
        """
        # Get combined ignore patterns (default + user configured)
        ignore_patterns = config.get("ignore_patterns", [])

        # Check against all patterns
        for pattern in ignore_patterns:
            if file_path.match(pattern):
                logger.info(f"Skipping ignored file: {file_path} (matched {pattern})")
                return True
            if any(
                part == pattern for part in file_path.parts
            ):  # Check parent directories
                logger.info(
                    f"Skipping ignored directory: {file_path} (matched {pattern})"
                )
                return True

        # Check against user-defined directory exclusions
        ignored_directories = config.get("ignored_directories", [])
        for ignored_dir in ignored_directories:
            ignored_path = Path(ignored_dir).resolve()
            try:
                if (
                    ignored_path in file_path.resolve().parents
                    or ignored_path == file_path.resolve()
                ):
                    logger.info(
                        f"Skipping file in ignored directory: {file_path} (in {ignored_dir})"
                    )
                    return True
            except (FileNotFoundError, RuntimeError):
                continue

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
