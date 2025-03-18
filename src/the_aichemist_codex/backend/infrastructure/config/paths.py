"""
Implementation of the ProjectPaths interface.

This module provides concrete implementation for path resolution
and management, which is essential for breaking circular dependencies
between settings and directory_manager.
"""

import os
from pathlib import Path

from ...core.constants import DEFAULT_DIRS
from ...core.interfaces import ProjectPaths


class ProjectPathsImpl(ProjectPaths):
    """Concrete implementation of the ProjectPaths interface."""

    def __init__(self):
        """Initialize the ProjectPathsImpl instance."""
        self._project_root = self._find_project_root()

    def _find_project_root(self) -> Path:
        """Find the project root directory based on the location of this file."""
        current_dir = Path(__file__).resolve().parent
        # Move up until we find the the_aichemist_codex directory
        while (
            current_dir.name != "the_aichemist_codex"
            and current_dir.parent != current_dir
        ):
            current_dir = current_dir.parent

        # If we reached the root without finding the marker, use the current directory
        if current_dir.name != "the_aichemist_codex":
            # Fallback to using the src directory if it exists
            current_dir = Path.cwd()
            if (current_dir / "src" / "the_aichemist_codex").exists():
                current_dir = current_dir / "src" / "the_aichemist_codex"

        return current_dir

    def get_project_root(self) -> Path:
        """Return the project root directory."""
        return self._project_root

    def get_cache_dir(self) -> Path:
        """Return the cache directory."""
        cache_dir = self._project_root / DEFAULT_DIRS["cache"]
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    def resolve_path(self, path: str, base_dir: Path | None = None) -> Path:
        """Resolve a path relative to the specified base directory."""
        # If it's an absolute path, return it directly
        if os.path.isabs(path):
            return Path(path).resolve()

        # Otherwise, resolve it relative to the base directory or project root
        base = base_dir or self._project_root
        return (base / path).resolve()
