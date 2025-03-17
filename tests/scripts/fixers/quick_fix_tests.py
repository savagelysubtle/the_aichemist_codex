#!/usr/bin/env python
"""
Quick script to fix the most common test issues:
1. Adding 'async' keyword to test functions that use 'await'
2. Ensuring the '@pytest.mark.asyncio' marker is present for async tests

Run this script from the project root:
python backend/tests/quick_fix_tests.py [directory]
"""

import os
import re
import sys


def process_file(file_path):
    """Process a test file and fix async issues."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return False

    # Skip if there are no await statements
    if "await " not in content:
        return False

    # Check for functions with await that aren't async
    modified = False
    lines = content.split("\n")

    # First, identify all the test functions
    test_functions = []
    awaits_by_function = {}

    current_function = None
    for i, line in enumerate(lines):
        if re.match(r"\s*def\s+test_\w+\s*\(", line):
            current_function = line.strip()
            test_functions.append((i, current_function))
            awaits_by_function[current_function] = []
        elif current_function and "await " in line:
            awaits_by_function[current_function].append(i)

    # Process each function with awaits
    for i, func_def in test_functions:
        # Skip if already async
        if "async def" in func_def:
            continue

        # Check if the function has awaits
        if not awaits_by_function[func_def]:
            continue

        # Replace 'def' with 'async def'
        lines[i] = lines[i].replace("def ", "async def ")
        modified = True

        # Get the indentation
        indent_match = re.match(r"(\s*)", lines[i])
        indent = indent_match.group(1) if indent_match else ""

        # Ensure we have the asyncio marker
        has_asyncio = False
        j = i - 1
        while j >= 0 and j >= i - 5:  # Check a few lines up
            if "@pytest.mark.asyncio" in lines[j]:
                has_asyncio = True
                break
            if not lines[j].strip() or (
                lines[j].strip() and not lines[j].strip().startswith("@")
            ):
                break
            j -= 1

        if not has_asyncio:
            # Insert the asyncio marker before the function
            lines.insert(i, f"{indent}@pytest.mark.asyncio")
            modified = True

    if modified:
        # Write the modified content back
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            return True
        except Exception as e:
            print(f"Error writing to {file_path}: {e}")
            return False

    return False


def find_test_files(directory):
    """Find all test files in a directory."""
    test_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(os.path.join(root, file))
    return test_files


def main():
    """Main entry point."""
    # Get base directory
    if len(sys.argv) > 1:
        base_dir = os.path.join("backend/tests", sys.argv[1])
    else:
        base_dir = "backend/tests"

    if not os.path.exists(base_dir):
        print(f"Directory not found: {base_dir}")
        return 1

    # Find test files
    test_files = find_test_files(base_dir)
    print(f"Found {len(test_files)} test files in {base_dir}")

    # Process each file
    fixed_files = 0
    for file_path in test_files:
        if process_file(file_path):
            print(f"Fixed async issues in {file_path}")
            fixed_files += 1

    print(f"\nFixed {fixed_files} of {len(test_files)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
