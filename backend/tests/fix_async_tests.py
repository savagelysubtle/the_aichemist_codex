#!/usr/bin/env python
"""
Script to fix async test syntax issues in test files.

This script scans all test files and fixes the following syntax issues:
1. Duplicate @pytest.mark.asyncio markers
2. Missing 'async' keyword in function definition when 'await' is used
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


def fix_async_test_syntax(file_path):
    """Fix async test syntax in the given file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"Could not decode {file_path} as UTF-8, skipping...")
        return False, 0, 0

    # Check if the file has issues
    has_await = "await " in content
    has_duplicate_asyncio = re.search(
        r"@pytest\.mark\.asyncio\s+@pytest\.mark\.asyncio", content
    )
    missing_async = re.search(r"def\s+test_\w+.*\n.*\s+await\s+", content)

    if not (has_await and (has_duplicate_asyncio or missing_async)):
        return False, 0, 0

    # Keep track of changes made
    duplicate_fixes = 0
    missing_async_fixes = 0

    # Remove duplicate @pytest.mark.asyncio
    if has_duplicate_asyncio:
        content_before = content
        content = re.sub(
            r"@pytest\.mark\.asyncio\s+@pytest\.mark\.asyncio",
            "@pytest.mark.asyncio",
            content,
        )
        duplicate_fixes += content_before.count("@pytest.mark.asyncio") - content.count(
            "@pytest.mark.asyncio"
        )

    # Add 'async' keyword to function definitions that use 'await'
    if missing_async:
        # Pattern to find function definitions that need 'async'
        pattern = r"(def\s+test_\w+.*\n.*\s+await\s+)"

        # Find all matches
        matches = re.finditer(pattern, content, re.MULTILINE)

        # Process each match individually
        for match in matches:
            func_def = match.group(1)
            if "async def" not in func_def:
                # Replace the function definition with 'async def'
                new_func_def = func_def.replace("def ", "async def ", 1)
                content = content.replace(func_def, new_func_def)
                missing_async_fixes += 1

    # Write the fixed content back to the file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return True, duplicate_fixes, missing_async_fixes


def main():
    """Main entry point."""
    # Get the base directory
    base_dir = Path(__file__).parent

    # Find all test files
    test_files = find_test_files(base_dir)
    print(f"Found {len(test_files)} test files")

    # Fix async test syntax in each file
    total_fixed_files = 0
    total_duplicate_fixes = 0
    total_missing_async_fixes = 0

    for file_path in test_files:
        try:
            fixed, duplicate_fixes, missing_async_fixes = fix_async_test_syntax(
                file_path
            )
            if fixed:
                changes = []
                if duplicate_fixes > 0:
                    changes.append(f"{duplicate_fixes} duplicate asyncio markers")
                if missing_async_fixes > 0:
                    changes.append(f"{missing_async_fixes} missing 'async' keywords")

                print(f"Fixed {', '.join(changes)} in {file_path}")
                total_fixed_files += 1
                total_duplicate_fixes += duplicate_fixes
                total_missing_async_fixes += missing_async_fixes
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    print("\nSummary:")
    print(f"- Fixed issues in {total_fixed_files} files")
    print(f"- Removed {total_duplicate_fixes} duplicate asyncio markers")
    print(f"- Added {total_missing_async_fixes} missing 'async' keywords")
    print(f"- {len(test_files) - total_fixed_files} files were already correct")

    return 0


if __name__ == "__main__":
    sys.exit(main())
