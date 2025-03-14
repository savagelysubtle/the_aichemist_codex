#!/usr/bin/env python
"""
Cleanup script for temporary directories and files created by The Aichemist Codex.
This script will remove temporary directories and outdated log files.
"""

import logging
import os
import shutil
import sys
from pathlib import Path

# Add the project root to the path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.append(str(project_root))

# Import the central logging system
from backend.config.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def cleanup_temp_directories():
    """Clean up temporary directories created by the application."""
    # Root directory of the project
    root_dir = project_root

    # Patterns that identify temporary directories
    temp_patterns = [
        "CodingPython_Projectsthe_aichemist_codextmp",
        "tmp",
        "temp",
        "logs0",
        "logs1",
        "log_",
        "test_logs_",
    ]

    # Find all potential temporary directories
    potential_temp_dirs = []

    # The known problematic directory
    known_tmp_dir = root_dir / "CodingPython_Projectsthe_aichemist_codextmp"
    if known_tmp_dir.exists():
        potential_temp_dirs.append(known_tmp_dir)

    # Look for other potential temp directories
    for pattern in temp_patterns:
        for item in root_dir.glob(f"**/*{pattern}*"):
            if item.is_dir() and item not in potential_temp_dirs:
                # Exclude protected directories
                if not any(
                    protected in str(item)
                    for protected in ["data/logs", "data/test_logs", "venv", ".git"]
                ):
                    potential_temp_dirs.append(item)

    # Sort directories by depth to remove children before parents
    potential_temp_dirs.sort(key=lambda x: len(str(x).split(os.sep)), reverse=True)

    # Process each potential temporary directory
    for tmp_dir in potential_temp_dirs:
        logger.info(f"Found potential temporary directory: {tmp_dir}")

        # Auto-remove known temporary directories
        is_known_temp = any(
            p in str(tmp_dir)
            for p in ["CodingPython_Projectsthe_aichemist_codextmp", "logs0", "logs1"]
        )

        if is_known_temp:
            try:
                logger.info(f"Removing known temporary directory: {tmp_dir}")
                shutil.rmtree(tmp_dir)
                print(f"✅ Removed temporary directory: {tmp_dir}")
            except Exception as e:
                logger.error(f"Failed to remove temporary directory {tmp_dir}: {e}")
                print(f"❌ Failed to remove {tmp_dir}: {e}")
        else:
            # For other directories, ask for confirmation
            choice = input(f"Remove temporary directory {tmp_dir}? (y/n): ")
            if choice.lower() == "y":
                try:
                    shutil.rmtree(tmp_dir)
                    print(f"✅ Removed: {tmp_dir}")
                except Exception as e:
                    logger.error(f"Failed to remove {tmp_dir}: {e}")
                    print(f"❌ Failed to remove {tmp_dir}: {e}")


def cleanup_temp_logs():
    """Clean up temporary log files that might be scattered around."""
    # Root directory of the project
    root_dir = project_root

    # Look for stray log files
    log_files = list(root_dir.glob("**/*.log"))

    # Filter out logs in the primary log directory
    primary_log_dir = root_dir / "data" / "logs"
    log_files = [f for f in log_files if primary_log_dir not in f.parents]

    if not log_files:
        return

    print(f"Found {len(log_files)} potential stray log files.")
    choice = input("Would you like to see and clean them up? (y/n): ")

    if choice.lower() == "y":
        for log_file in log_files:
            print(f"Log file: {log_file}")
            choice = input(f"Remove log file {log_file}? (y/n): ")
            if choice.lower() == "y":
                try:
                    os.remove(log_file)
                    print(f"✅ Removed: {log_file}")
                except Exception as e:
                    logger.error(f"Failed to remove {log_file}: {e}")
                    print(f"❌ Failed to remove {log_file}: {e}")


def main():
    print("🧹 Starting cleanup of temporary directories and files...")
    cleanup_temp_directories()
    cleanup_temp_logs()
    print("✨ Cleanup completed!")


if __name__ == "__main__":
    main()
