"""
Implementation of the FileValidator interface.

This module provides concrete implementation for file validation operations,
addressing circular dependencies with safety and other modules.
"""

import os
import re
from pathlib import Path

from ...core.exceptions import UnsafePathError
from ...core.interfaces import FileValidator
from ...registry import Registry


class FileValidatorImpl(FileValidator):
    """Concrete implementation of the FileValidator interface."""

    def __init__(self):
        """Initialize the FileValidator instance."""
        self._config = Registry.get_instance().config_provider
        self._paths = Registry.get_instance().project_paths
        self._unsafe_patterns: list[str] = []
        self._allowed_paths: set[Path] = set()
        self._blocked_extensions: set[str] = set()
        self._load_security_config()

    def _load_security_config(self) -> None:
        """Load security configuration settings."""
        # Get unsafe path patterns from config
        security_config = self._config.get_config("security", {})

        # Load unsafe patterns that should be blocked
        self._unsafe_patterns = security_config.get(
            "unsafe_patterns",
            [
                r"\.\./",  # Directory traversal
                r"~/",  # Home directory
                r"^/",  # Absolute paths
                r'[<>:"|?*]',  # Invalid characters for most filesystems
            ],
        )

        # Load allowed base paths
        allowed_paths = security_config.get("allowed_paths", [])
        self._allowed_paths = {Path(path).resolve() for path in allowed_paths}

        # Add default project paths to allowed paths
        self._allowed_paths.add(self._paths.get_project_root())
        self._allowed_paths.add(self._paths.get_cache_dir())
        self._allowed_paths.add(self._paths.get_data_dir())
        self._allowed_paths.add(self._paths.get_config_dir())

        # Load blocked extensions
        self._blocked_extensions = set(
            security_config.get(
                "blocked_extensions",
                [".exe", ".bat", ".cmd", ".com", ".dll", ".vbs", ".js", ".ps1", ".sh"],
            )
        )

    def is_path_safe(self, path: str) -> bool:
        """
        Check if a file path is safe to access.

        Args:
            path: The file path to validate

        Returns:
            True if the path is safe, False otherwise
        """
        # Check if path contains unsafe patterns
        for pattern in self._unsafe_patterns:
            if re.search(pattern, path):
                return False

        # Check if file has blocked extension
        _, ext = os.path.splitext(path)
        if ext.lower() in self._blocked_extensions:
            return False

        # Check if path is within allowed paths
        path_obj = Path(path).resolve()

        # Check if path is within any allowed path
        for allowed_path in self._allowed_paths:
            try:
                # Use is_relative_to in Python 3.9+, or this equivalent for earlier versions
                path_obj.relative_to(allowed_path)
                return True
            except ValueError:
                continue

        return False

    def ensure_path_safe(self, path: str) -> str:
        """
        Ensure a file path is safe to access.

        Args:
            path: The file path to validate

        Returns:
            The validated path

        Raises:
            UnsafePathError: If the path is not safe
        """
        if not self.is_path_safe(path):
            raise UnsafePathError(f"Unsafe path: {path}")
        return path

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a filename to make it safe for use in a file system.

        Args:
            filename: The filename to sanitize

        Returns:
            A sanitized filename
        """
        # Remove characters that are invalid for most filesystems
        sanitized = re.sub(r'[<>:"/\\|?*]', "_", filename)

        # Limit length to avoid issues with some filesystems
        if len(sanitized) > 255:
            sanitized = sanitized[:255]

        return sanitized
