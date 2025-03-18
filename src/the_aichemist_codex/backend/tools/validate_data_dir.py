#!/usr/bin/env python
"""
Data Directory Validation Tool.

This script checks the configuration of the data directory and verifies that
all required subdirectories exist and are accessible. It uses the registry
pattern to avoid circular dependencies.
"""

import logging
import os
import sys
from pathlib import Path

from ..bootstrap import bootstrap
from ..registry import Registry

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger("data_dir_validator")


def check_directory(directory: Path, name: str, required: bool = True) -> bool:
    """
    Check if a directory exists and is accessible.

    Args:
        directory: The directory to check
        name: A descriptive name for the directory
        required: Whether the directory is required (if False, warning instead of error)

    Returns:
        True if the directory is accessible or not required, False otherwise
    """
    try:
        if not directory.exists():
            if required:
                logger.error(f"{name} directory does not exist: {directory}")
                return False
            else:
                logger.warning(f"{name} directory does not exist: {directory}")
                return True

        # Check if directory is readable and writable
        if not os.access(directory, os.R_OK):
            logger.error(f"{name} directory is not readable: {directory}")
            return False

        if not os.access(directory, os.W_OK):
            logger.error(f"{name} directory is not writable: {directory}")
            return False

        logger.info(f"{name} directory is accessible: {directory}")
        return True
    except Exception as e:
        logger.error(f"Error checking {name} directory: {e}")
        return False


def validate_data_directory() -> bool:
    """
    Validate the data directory configuration.

    Checks:
    1. If environment variables are set
    2. If all required directories exist and are accessible

    Returns:
        bool: True if validation passes, False otherwise
    """
    # Bootstrap the application
    bootstrap()

    # Get registry and paths
    registry = Registry.get_instance()
    paths = registry.project_paths

    # Check environment variables
    if "AICHEMIST_ROOT_DIR" in os.environ:
        logger.info(f"AICHEMIST_ROOT_DIR is set to: {os.environ['AICHEMIST_ROOT_DIR']}")

    if "AICHEMIST_DATA_DIR" in os.environ:
        logger.info(f"AICHEMIST_DATA_DIR is set to: {os.environ['AICHEMIST_DATA_DIR']}")

    # Log detected paths
    project_root = paths.get_project_root()
    data_dir = paths.get_data_dir()

    logger.info(f"Project root detected as: {project_root}")
    logger.info(f"Data directory detected as: {data_dir}")

    # Validate required directories
    valid = True
    valid &= check_directory(data_dir, "Data")
    valid &= check_directory(paths.get_cache_dir(), "Cache")
    valid &= check_directory(paths.get_logs_dir(), "Log")
    valid &= check_directory(paths.get_data_dir() / "export", "Export")
    valid &= check_directory(paths.get_data_dir() / "versions", "Version")

    # Check optional directories
    backup_dir = data_dir / "backup"
    if backup_dir.exists():
        valid &= check_directory(backup_dir, "Backup", required=False)

    trash_dir = data_dir / "trash"
    if trash_dir.exists():
        valid &= check_directory(trash_dir, "Trash", required=False)

    notifications_dir = data_dir / "notifications"
    if notifications_dir.exists():
        valid &= check_directory(notifications_dir, "Notifications", required=False)

    return valid


def main() -> int:
    """
    Run the data directory validation.

    Returns:
        int: 0 if validation passes, 1 if it fails
    """
    logger.info("Validating data directory configuration...")

    try:
        if validate_data_directory():
            logger.info("Data directory validation passed!")
            return 0
        else:
            logger.error("Data directory validation failed!")
            return 1
    except Exception as e:
        logger.error(f"Error during validation: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
