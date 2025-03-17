"""
Utility for validating and repairing the data directory structure.

This module provides functions to check if the data directory structure
is correct and fix any missing or incorrect components.
"""

import logging
import os

from the_aichemist_codex.backend.config.settings import directory_manager

logger = logging.getLogger(__name__)


def validate_data_directory() -> dict[str, bool]:
    """
    Validate the data directory structure, checking all required subdirectories.

    Returns:
        Dict[str, bool]: Status of each required directory
    """
    results = {}

    # Check main data directory
    data_dir = directory_manager.base_dir
    results["base"] = data_dir.exists() and data_dir.is_dir()

    # Check all standard subdirectories
    for subdir in directory_manager.STANDARD_DIRS:
        dir_path = directory_manager.get_dir(subdir)
        results[subdir] = dir_path.exists() and dir_path.is_dir()

    # Check for required files
    rollback_path = directory_manager.get_file_path("rollback.json")
    results["rollback.json"] = rollback_path.exists() and rollback_path.is_file()

    version_metadata_path = directory_manager.get_file_path("version_metadata.json")
    results["version_metadata.json"] = (
        version_metadata_path.exists() and version_metadata_path.is_file()
    )

    return results


def repair_data_directory() -> list[str]:
    """
    Repair the data directory structure, creating any missing components.

    Returns:
        List[str]: List of fixes applied
    """
    fixes = []
    validation = validate_data_directory()

    # Ensure base directory exists
    if not validation["base"]:
        os.makedirs(directory_manager.base_dir, exist_ok=True)
        fixes.append(f"Created base data directory at {directory_manager.base_dir}")

    # Ensure all standard subdirectories exist
    for subdir in directory_manager.STANDARD_DIRS:
        if not validation.get(subdir, False):
            dir_path = directory_manager.get_dir(subdir)
            os.makedirs(dir_path, exist_ok=True)
            fixes.append(f"Created {subdir} directory at {dir_path}")

    # Create required files if missing
    if not validation.get("rollback.json", False):
        rollback_path = directory_manager.get_file_path("rollback.json")
        with open(rollback_path, "w") as f:
            f.write("{}\n")  # Empty JSON object
        fixes.append(f"Created empty rollback.json at {rollback_path}")

    if not validation.get("version_metadata.json", False):
        version_metadata_path = directory_manager.get_file_path("version_metadata.json")
        with open(version_metadata_path, "w") as f:
            f.write("{}\n")  # Empty JSON object
        fixes.append(f"Created empty version_metadata.json at {version_metadata_path}")

    return fixes


def get_directory_status() -> tuple[bool, dict[str, bool], list[str]]:
    """
    Get the complete status of the data directory.

    Returns:
        Tuple[bool, Dict[str, bool], List[str]]:
            - Overall status (True if valid)
            - Status of each component
            - List of issues found
    """
    validation = validate_data_directory()
    issues = []

    # Compile list of issues
    for component, status in validation.items():
        if not status:
            if component == "base":
                issues.append(
                    f"Base data directory missing: {directory_manager.base_dir}"
                )
            elif component in directory_manager.STANDARD_DIRS:
                issues.append(f"Directory '{component}' missing")
            else:
                issues.append(f"File '{component}' missing")

    # Overall status is True only if all components are valid
    overall_status = all(validation.values())

    return overall_status, validation, issues
