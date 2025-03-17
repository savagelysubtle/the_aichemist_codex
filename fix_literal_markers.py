#!/usr/bin/env python3
"""
Script to fix files with literal '@pytest.mark.[a-z]+' markers.
This pattern appears as a literal string in the files, not as a regex pattern.
"""

import os
from pathlib import Path


def fix_file(file_path: Path) -> bool:
    """
    Fix a file with literal '@pytest.mark.[a-z]+' markers.

    Args:
        file_path: Path to the file to fix

    Returns:
        bool: True if the file was modified, False otherwise
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()

        modified = False
        for i, line in enumerate(lines):
            if "@pytest.mark.[a-z]+" in line:
                lines[i] = line.replace("@pytest.mark.[a-z]+", "@pytest.mark.unit")
                modified = True

        if modified:
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            return True
        return False

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Main function to fix files with literal '@pytest.mark.[a-z]+' markers."""
    tests_dir = Path(__file__).parent / "tests"
    print(f"Scanning for Python files in {tests_dir}")

    files_fixed = 0
    total_files = 0

    # Walk through all Python files in the tests directory
    for root, _, files in os.walk(tests_dir):
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
