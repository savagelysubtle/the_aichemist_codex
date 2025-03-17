#!/usr/bin/env python3
"""
Script to fix issues in test files:
1. Replace duplicate 'async async def' with 'async def'
2. Fix broken pytest markers (replace @pytest.mark.[a-z]+ with @pytest.mark.unit)
"""

import os
import re
from pathlib import Path

# Define the patterns to search for and their replacements
PATTERNS = [
    (r"async\s+async\s+def", "async def"),
    (
        r"@pytest\.mark\.\[a-z\]\+",
        "@pytest.mark.unit",
    ),  # This pattern likely won't match
]

# Path to the test directory
TESTS_DIR = Path(__file__).parent / "tests"


def fix_file(file_path: Path) -> bool:
    """
    Fix issues in a file.

    Args:
        file_path: Path to the file to fix

    Returns:
        bool: True if the file was modified, False otherwise
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Check for the duplicate async pattern
        modified_content = re.sub(r"async\s+async\s+def", "async def", content)

        # Check for the broken pytest marker - using line-by-line approach
        lines = modified_content.splitlines()
        for i, line in enumerate(lines):
            if "@pytest.mark.[a-z]+" in line:
                lines[i] = line.replace("@pytest.mark.[a-z]+", "@pytest.mark.unit")

        modified_content = "\n".join(lines)

        # If no changes were made, return False
        if content == modified_content:
            return False

        # Write the modified content back to the file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(modified_content)

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
