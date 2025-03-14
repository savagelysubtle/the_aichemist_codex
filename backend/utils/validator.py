"""Provides validation and general utilities."""

from pathlib import Path


def get_project_name(directory: Path) -> str:
    """Returns the project name based on the directory name."""
    return directory.name
