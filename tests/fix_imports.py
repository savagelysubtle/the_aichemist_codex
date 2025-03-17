#!/usr/bin/env python
"""
Script to fix import statements in test files.

This script updates import statements from 'backend.src' to 'the_aichemist_codex.backend'
to match the new module structure.

Run this script from the project root:
    python tests/fix_imports.py
"""

import os
import re
from pathlib import Path


def find_test_files(base_dir: Path) -> list[Path]:
    """Find all Python test files in the given directory and subdirectories."""
    test_files = []

    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                test_files.append(file_path)

    return test_files


def fix_imports(file_path: Path) -> tuple[int, int]:
    """
    Fix import statements in the given file.

    Args:
        file_path: Path to the file to fix

    Returns:
        tuple: (number of files processed, number of imports fixed)
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Replace 'backend.src' with 'the_aichemist_codex.backend'
        pattern = r"from\s+backend\.src\."
        replacement = "from the_aichemist_codex.backend."
        new_content, num_replacements = re.subn(pattern, replacement, content)

        # Also replace 'import the_aichemist_codex.backend.' with 'import the_aichemist_codex.backend.'
        pattern2 = r"import\s+backend\.src\."
        replacement2 = "import the_aichemist_codex.backend."
        new_content, num_replacements2 = re.subn(pattern2, replacement2, new_content)

        total_replacements = num_replacements + num_replacements2

        if total_replacements > 0:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Fixed {total_replacements} imports in {file_path}")
            return 1, total_replacements

        return 1, 0

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return 0, 0


def main():
    """Main function to find and fix test files."""
    # Get the project root directory
    project_root = Path(__file__).resolve().parent.parent
    tests_dir = project_root / "tests"

    print(f"Searching for test files in {tests_dir}...")
    test_files = find_test_files(tests_dir)
    print(f"Found {len(test_files)} Python files")

    total_files_processed = 0
    total_imports_fixed = 0

    for file_path in test_files:
        files_processed, imports_fixed = fix_imports(file_path)
        total_files_processed += files_processed
        total_imports_fixed += imports_fixed

    print("\nSummary:")
    print(f"- Files processed: {total_files_processed}")
    print(f"- Import statements fixed: {total_imports_fixed}")


if __name__ == "__main__":
    main()
