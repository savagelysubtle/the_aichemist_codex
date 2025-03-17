#!/usr/bin/env python
"""
Script to add the 'async' keyword to test functions that contain 'await' statements.

This script helps fix the common syntax error:
    def test_function():
        await something()

By replacing it with:
    async def test_function():
        await something()
"""

import os
import re
import sys
from pathlib import Path


def find_test_files(base_dir):
    """Find all test files in the given directory."""
    test_files = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(os.path.join(root, file))
    return test_files


def add_async_to_functions(file_path):
    """Add the 'async' keyword to test functions that use 'await'."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"Could not decode {file_path} as UTF-8, skipping...")
        return False, 0

    # Check if the file has 'await' statements
    if "await " not in content:
        return False, 0

    # Define a pattern to identify test functions that use 'await' but aren't declared as async
    pattern = r"def\s+(test_\w+).*?\).*?:\s*?(?:.*?\n)*?.*?await\s+"

    # Get all matches for test functions
    matches = list(re.finditer(pattern, content, re.DOTALL))
    if not matches:
        return False, 0

    # Count of functions fixed
    fixed_count = 0

    # Process the file content to add 'async' to appropriate function definitions
    for match in reversed(matches):  # Process in reverse to avoid position shifts
        function_name = match.group(1)
        function_start = match.start()

        # Check if it's already async
        pre_function = content[max(0, function_start - 20) : function_start]
        if "async def" in pre_function:
            continue

        # Get the exact def line
        match_text = match.group(0)
        def_line_end = match_text.find(":") + 1
        def_line = match_text[:def_line_end]

        # Replace with async version
        async_def_line = def_line.replace("def ", "async def ", 1)
        content = content.replace(def_line, async_def_line, 1)
        fixed_count += 1

        print(f"  - Added async to function: {function_name}")

    # Write the fixed content back to the file if changes were made
    if fixed_count > 0:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    return True, fixed_count


def main():
    """Main entry point."""
    # Get the base directory
    base_dir = Path(__file__).parent

    # Find all test files
    test_files = find_test_files(base_dir)
    print(f"Found {len(test_files)} test files")

    # Process each file
    total_files_fixed = 0
    total_functions_fixed = 0

    for file_path in test_files:
        try:
            processed, function_count = add_async_to_functions(file_path)
            if processed and function_count > 0:
                print(f"Fixed {function_count} functions in {file_path}")
                total_files_fixed += 1
                total_functions_fixed += function_count
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    print("\nSummary:")
    print(
        f"- Added 'async' keyword to {total_functions_fixed} functions in {total_files_fixed} files"
    )
    print(
        f"- {len(test_files) - total_files_fixed} files were already correct or didn't need changes"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
