"""Ensures file operations remain within safe directories."""

from pathlib import Path


class SafeDirectoryScanner:
    """Provides safe file access utilities."""

    @staticmethod
    def is_safe_path(target: Path, base: Path) -> bool:
        """Ensures that a target path is within the base directory."""
        try:
            return base.resolve() in target.resolve().parents
        except (FileNotFoundError, RuntimeError):
            return False
