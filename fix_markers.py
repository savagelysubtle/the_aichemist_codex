#!/usr/bin/env python3
"""
Script to fix pytest marker issues in test files.
Replaces all instances of '@pytest.mark.[a-z]+' with '@pytest.mark.unit'
"""

import os
from pathlib import Path


def fix_file(file_path: Path) -> tuple[bool, int]:
    """
    Fix a file by replacing '@pytest.mark.[a-z]+' with '@pytest.mark.unit'.

    Args:
        file_path: Path to the file to fix

    Returns:
        tuple: (was_modified, number_of_replacements)
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Count the occurrences before replacing
        count = content.count("@pytest.mark.[a-z]+")

        # Replace the literal pattern
        modified_content = content.replace("@pytest.mark.[a-z]+", "@pytest.mark.unit")

        # Only write to the file if changes were made
        if modified_content != content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(modified_content)
            return True, count

        return False, 0

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False, 0


def main():
    """Main function to fix all files with marker issues."""
    tests_dir = Path(__file__).parent / "tests"
    print(f"Scanning for Python files in {tests_dir}")

    files_fixed = 0
    total_replacements = 0
    total_files = 0

    # Walk through all Python files in the tests directory
    for root, _, files in os.walk(tests_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                total_files += 1

                was_modified, replacements = fix_file(file_path)
                if was_modified:
                    files_fixed += 1
                    total_replacements += replacements
                    print(f"Fixed: {file_path} - {replacements} replacements")

    print("\nSummary:")
    print(f"Total Python files scanned: {total_files}")
    print(f"Files fixed: {files_fixed}")
    print(f"Total replacements: {total_replacements}")


if __name__ == "__main__":
    main()
