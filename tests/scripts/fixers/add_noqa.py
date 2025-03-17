#!/usr/bin/env python
"""
Script to add # noqa: S101 to all assert statements in test files.  # noqa: S101
This addresses the linter rule that flags assert statements in production code.  # noqa: S101
"""

import os
import re
from pathlib import Path


def add_noqa_to_file(file_path):
    """Add noqa directives to assert statements in a file."""  # noqa: S101
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Pattern to find assert statements not followed by noqa directive  # noqa: S101
    pattern = r"(assert\s+[^#\n]+)(?!\s*#\s*noqa:\s*S101)$"

    # Replace with the same statement + noqa directive
    modified_content = re.sub(pattern, r"\1  # noqa: S101", content, flags=re.MULTILINE)

    if content != modified_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(modified_content)
        return True
    return False


def process_tests_directory(directory_path):
    """Process all Python files in the tests directory."""
    tests_dir = Path(directory_path)
    count = 0
    files_modified = 0

    for root, _, files in os.walk(tests_dir):
        for file in files:
            if file.endswith(".py"):
                full_path = Path(root) / file
                if add_noqa_to_file(full_path):
                    files_modified += 1
                    print(f"Modified: {full_path}")

    print(f"Total files modified: {files_modified}")


if __name__ == "__main__":
    process_tests_directory("backend/tests")
