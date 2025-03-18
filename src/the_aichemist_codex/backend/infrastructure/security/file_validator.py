"""
Implementation of the FileValidator interface.

This module provides concrete implementation for file validation
and security checks, breaking circular dependencies between async_io,
safety, and config_loader modules.
"""

from pathlib import Path

from ...core.constants import UNSAFE_FILENAMES, UNSAFE_PATHS
from ...core.interfaces import FileValidator
from ...core.utils import sanitize_filename
from ...registry import Registry


class FileValidatorImpl(FileValidator):
    """Concrete implementation of the FileValidator interface."""

    def __init__(self):
        """Initialize the FileValidatorImpl instance."""
        self._unsafe_paths: set[str] = set(UNSAFE_PATHS)
        self._unsafe_filenames: set[str] = set(UNSAFE_FILENAMES)

    def is_safe_path(self, path: str, base_dir: Path | None = None) -> bool:
        """
        Check if a path is safe to access.

        Args:
            path: The path to check
            base_dir: Optional base directory to resolve relative paths against

        Returns:
            bool: True if the path is safe, False otherwise
        """
        try:
            # Get ProjectPaths from registry to resolve the path
            project_paths = Registry.get_instance().project_paths

            # Resolve the path
            resolved_path = project_paths.resolve_path(path, base_dir)

            # Check if the path is within one of the unsafe directories
            for unsafe_path in self._unsafe_paths:
                unsafe_path = Path(unsafe_path)
                try:
                    # Check if resolved_path is inside unsafe_path
                    resolved_path.relative_to(unsafe_path)
                    return False
                except ValueError:
                    # Not in this unsafe path, continue checking
                    pass

            # Check if the file name is in the unsafe list
            if resolved_path.name.lower() in self._unsafe_filenames:
                return False

            # Additional checks (e.g., check for suspicious symlinks)
            if resolved_path.is_symlink():
                # We could add more checks for symlinks if needed
                symlink_target = resolved_path.resolve()
                # Check if symlink target is unsafe
                for unsafe_path in self._unsafe_paths:
                    try:
                        symlink_target.relative_to(Path(unsafe_path))
                        return False
                    except ValueError:
                        pass

            # If all checks pass, the path is safe
            return True

        except Exception:
            # If any error occurs, consider it unsafe
            return False

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a filename to be safe for file operations.

        Args:
            filename: The filename to sanitize

        Returns:
            str: The sanitized filename
        """
        return sanitize_filename(filename)
