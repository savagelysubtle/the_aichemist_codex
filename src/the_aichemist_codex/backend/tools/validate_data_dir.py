#!/usr/bin/env python
"""
Data Directory Validation Tool.

This script checks the configuration of the data directory and verifies that
all required subdirectories exist and are accessible.
"""

import logging
import os
import sys

from the_aichemist_codex.backend.config.settings import (
    CACHE_DIR,
    DATA_DIR,
    EXPORT_DIR,
    LOG_DIR,
    PROJECT_ROOT,
    VERSION_DIR,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger("data_dir_validator")


def check_directory(directory, name, required=True):
    """Check if a directory exists and is accessible."""
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


def validate_data_directory():
    """
    Validate the data directory configuration.

    Checks:
    1. If environment variables are set
    2. If all required directories exist and are accessible

    Returns:
        bool: True if validation passes, False otherwise
    """
    # Check environment variables
    if "AICHEMIST_ROOT_DIR" in os.environ:
        logger.info(f"AICHEMIST_ROOT_DIR is set to: {os.environ['AICHEMIST_ROOT_DIR']}")

    if "AICHEMIST_DATA_DIR" in os.environ:
        logger.info(f"AICHEMIST_DATA_DIR is set to: {os.environ['AICHEMIST_DATA_DIR']}")

    # Log detected paths
    logger.info(f"Project root detected as: {PROJECT_ROOT}")
    logger.info(f"Data directory detected as: {DATA_DIR}")

    # Validate required directories
    valid = True
    valid &= check_directory(DATA_DIR, "Data")
    valid &= check_directory(CACHE_DIR, "Cache")
    valid &= check_directory(LOG_DIR, "Log")
    valid &= check_directory(EXPORT_DIR, "Export")
    valid &= check_directory(VERSION_DIR, "Version")

    # Check optional directories
    backup_dir = DATA_DIR / "backup"
    if backup_dir.exists():
        valid &= check_directory(backup_dir, "Backup", required=False)

    trash_dir = DATA_DIR / "trash"
    if trash_dir.exists():
        valid &= check_directory(trash_dir, "Trash", required=False)

    notifications_dir = DATA_DIR / "notifications"
    if notifications_dir.exists():
        valid &= check_directory(notifications_dir, "Notifications", required=False)

    return valid


def main():
    """Run the data directory validation."""
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
