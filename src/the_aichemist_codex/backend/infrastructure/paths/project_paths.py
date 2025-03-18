"""
Implementation of the ProjectPaths interface.

This module provides concrete implementation for project path management,
breaking the circular dependency between settings and directory_manager.
"""

import os
import platform
from pathlib import Path

from ...core.interfaces import ProjectPaths


class ProjectPathsImpl(ProjectPaths):
    """Concrete implementation of the ProjectPaths interface."""

    def __init__(self, custom_root: Path | None = None):
        """
        Initialize the ProjectPaths instance.

        Args:
            custom_root: Optional custom root directory path
        """
        self._project_root = self._determine_project_root(custom_root)
        self._app_data_dir = self._determine_app_data_dir()

        # Initialize path cache
        self._config_dir = self._app_data_dir / "config"
        self._cache_dir = self._app_data_dir / "cache"
        self._data_dir = self._app_data_dir / "data"
        self._logs_dir = self._app_data_dir / "logs"
        self._temp_dir = self._app_data_dir / "temp"

        # Ensure critical directories exist
        self._ensure_directories_exist()

    def _determine_project_root(self, custom_root: Path | None = None) -> Path:
        """
        Determine the project root directory.

        Args:
            custom_root: Optional custom root directory path

        Returns:
            Path to the project root directory
        """
        if custom_root:
            return custom_root.resolve()

        # First try environment variable
        env_root = os.environ.get("AICHEMIST_ROOT")
        if env_root:
            return Path(env_root).resolve()

        # Otherwise, use the location of this file as a reference
        # and go up the directory tree until we find the project root
        current_file = Path(__file__).resolve()

        # Navigate up from infrastructure/paths/project_paths.py
        # to the_aichemist_codex/backend
        backend_dir = current_file.parent.parent.parent

        # The project root should be the parent of backend
        return backend_dir.parent

    def _determine_app_data_dir(self) -> Path:
        """
        Determine the application data directory.

        Returns:
            Path to the application data directory
        """
        system = platform.system().lower()

        if system == "windows":
            base_dir = Path(
                os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
            )
        elif system == "darwin":  # macOS
            base_dir = Path.home() / "Library" / "Application Support"
        else:  # Linux and others
            xdg_data_home = os.environ.get("XDG_DATA_HOME")
            if xdg_data_home:
                base_dir = Path(xdg_data_home)
            else:
                base_dir = Path.home() / ".local" / "share"

        # Create app-specific data directory
        return base_dir / "the_aichemist_codex"

    def _ensure_directories_exist(self) -> None:
        """Ensure all critical directories exist."""
        for directory in [
            self._config_dir,
            self._cache_dir,
            self._data_dir,
            self._logs_dir,
            self._temp_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    def get_project_root(self) -> Path:
        """
        Get the project root directory.

        Returns:
            Path to the project root directory
        """
        return self._project_root

    def get_app_data_dir(self) -> Path:
        """
        Get the application data directory.

        Returns:
            Path to the application data directory
        """
        return self._app_data_dir

    def get_config_dir(self) -> Path:
        """
        Get the configuration directory.

        Returns:
            Path to the configuration directory
        """
        return self._config_dir

    def get_cache_dir(self) -> Path:
        """
        Get the cache directory.

        Returns:
            Path to the cache directory
        """
        return self._cache_dir

    def get_data_dir(self) -> Path:
        """
        Get the data directory.

        Returns:
            Path to the data directory
        """
        return self._data_dir

    def get_logs_dir(self) -> Path:
        """
        Get the logs directory.

        Returns:
            Path to the logs directory
        """
        return self._logs_dir

    def get_temp_dir(self) -> Path:
        """
        Get the temporary directory.

        Returns:
            Path to the temporary directory
        """
        return self._temp_dir

    def get_default_config_file(self) -> Path:
        """
        Get the default configuration file path.

        Returns:
            Path to the default configuration file
        """
        return self._config_dir / "config.yaml"

    def resolve_path(self, path: str, relative_to: Path | None = None) -> Path:
        """
        Resolve a path relative to a base directory.

        Args:
            path: The path to resolve
            relative_to: The base directory to resolve from (defaults to project root)

        Returns:
            The resolved path
        """
        if os.path.isabs(path):
            return Path(path).resolve()

        if relative_to is None:
            relative_to = self._project_root

        return (relative_to / path).resolve()

    def get_relative_path(self, path: str, base_path: Path | None = None) -> str:
        """
        Get a path relative to a base path.

        Args:
            path: The path to get relative
            base_path: The base path (defaults to project root)

        Returns:
            The relative path as a string
        """
        if base_path is None:
            base_path = self._project_root

        path_obj = Path(path).resolve()

        try:
            return str(path_obj.relative_to(base_path))
        except ValueError:
            # If the path is not relative to base_path, return the absolute path
            return str(path_obj)
