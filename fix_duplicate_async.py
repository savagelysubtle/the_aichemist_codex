#!/usr/bin/env python3
"""
Script to fix duplicate async keywords in test files.
This script will scan for "async async def" and replace it with "async def".
"""

import os
import re
from pathlib import Path

# Define the pattern to search for
PATTERN = r"async\s+async\s+def"
REPLACEMENT = "async def"

# Path to the test directory
TESTS_DIR = Path(__file__).parent / "tests"


def fix_file(file_path: Path) -> bool:
    """
    Fix duplicate async keywords in a file.

    Args:
        file_path: Path to the file to fix

    Returns:
        bool: True if the file was modified, False otherwise
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Check if the file contains the pattern
        if not re.search(PATTERN, content):
            return False

        # Replace all occurrences of the pattern
        new_content = re.sub(PATTERN, REPLACEMENT, content)

        # Write the modified content back to the file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Main function to scan and fix all Python files in the tests directory."""
    print(f"Scanning for Python files in {TESTS_DIR}")
    files_fixed = 0
    total_files = 0

    # Walk through all Python files in the tests directory
    for root, _, files in os.walk(TESTS_DIR):
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                total_files += 1

                if fix_file(file_path):
                    files_fixed += 1
                    print(f"Fixed: {file_path}")

    print("\nSummary:")
    print(f"Total Python files scanned: {total_files}")
    print(f"Files fixed: {files_fixed}")


if __name__ == "__main__":
    main()
