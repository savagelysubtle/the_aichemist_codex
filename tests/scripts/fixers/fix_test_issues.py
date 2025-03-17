#!/usr/bin/env python
"""
Script to fix common issues in test files:
1. Missing 'async' keyword for test functions using 'await'
2. Indentation problems, especially with pytest markers
3. Duplicate pytest markers
4. Syntax cleanups

Run this script from the project root to fix all test files:
    python backend/tests/fix_test_issues.py [optional_directory]
"""

import os
import re
import sys
from pathlib import Path


def find_test_files(base_dir: Path, target_dir: str | None = None) -> list[str]:
    """Find all test files in the given directory and subdirectories."""
    test_files = []

    # If target_dir is specified, use it as the base for search
    search_dir = os.path.join(base_dir, target_dir) if target_dir else base_dir
    search_dir = Path(search_dir)

    # Check if the directory exists
    if not search_dir.exists() or not search_dir.is_dir():
        print(f"Directory not found: {search_dir}")
        return []

    for root, _, files in os.walk(search_dir):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(os.path.join(root, file))
    return test_files


def fix_indentation_issues(content: str) -> tuple[str, int]:
    """Fix indentation issues in pytest markers."""
    if "@pytest.mark" not in content:
        return content, 0

    # Common patterns for indentation issues
    patterns = [
        # Fix unexpected indentation in markers
        (
            r"\n(\s+)@pytest\.mark\.([a-z]+)\s*\n\s+@pytest\.mark",
            r"\n\1@pytest.mark.\2\n\1@pytest.mark",
        ),
        # Fix missing indentation before test function
        (r"@pytest\.mark\.[a-z]+\s*\ndef", r"@pytest.mark.[a-z]+\n\ndef"),
        # Ensure consistent spacing between markers
        (
            r"@pytest\.mark\.[a-z]+\s*\n\s*@pytest\.mark",
            r"@pytest.mark.[a-z]+\n@pytest.mark",
        ),
    ]

    fixes = 0
    for pattern, replacement in patterns:
        old_content = content
        try:
            # Use count to track changes
            content = re.sub(pattern, replacement, content)
            if content != old_content:
                fixes += 1
        except Exception as e:
            print(f"Error applying pattern {pattern}: {e}")

    return content, fixes


def fix_duplicate_markers(content: str) -> tuple[str, int]:
    """Remove duplicate pytest markers."""
    if "@pytest.mark" not in content:
        return content, 0

    # Pattern for duplicate markers
    duplicate_marker_pattern = r"(@pytest\.mark\.[a-z]+)\s+\1"

    # Count occurrences before replacement
    count_before = len(re.findall(r"@pytest\.mark\.[a-z]+", content))

    # Replace duplicate markers
    content = re.sub(duplicate_marker_pattern, r"\1", content)

    # Count occurrences after replacement
    count_after = len(re.findall(r"@pytest\.mark\.[a-z]+", content))

    return content, count_before - count_after


def add_async_to_functions(content: str) -> tuple[str, set[str]]:
    """Add 'async' keyword to test functions that use 'await'."""
    if "await" not in content:
        return content, set()

    # Get all function defs with await that aren't already async
    pattern = r"(def\s+(test_\w+).*?\).*?:)(?:.*?\n)*?(?:.*?await)"

    # Find all matches for test functions that need 'async'
    matches = list(re.finditer(pattern, content, re.DOTALL))

    # Track function names that were fixed
    fixed_functions = set()

    # Process matches in reverse to avoid position shifts
    for match in reversed(matches):
        full_def = match.group(1)
        func_name = match.group(2)

        # Skip if it's already marked async
        prefix_start = max(0, match.start() - 30)
        prefix = content[prefix_start : match.start()]
        if "async def" in prefix:
            continue

        # Replace with async version
        if "async " not in full_def:
            new_full_def = full_def.replace("def ", "async def ", 1)
            content = content.replace(full_def, new_full_def)
            fixed_functions.add(func_name)

    return content, fixed_functions


def ensure_asyncio_marker(content: str, fixed_functions: set[str]) -> tuple[str, int]:
    """Ensure that async test functions have the asyncio marker."""
    if not fixed_functions or "async def test_" not in content:
        return content, 0

    added_markers = 0

    # For each fixed function, check if it has the asyncio marker
    for func_name in fixed_functions:
        # Find the function definition
        pattern = rf"(.*?)(async def {func_name})"
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            continue

        # Check if the preceding content has the asyncio marker
        preceding = match.group(1)
        if "@pytest.mark.asyncio" not in preceding.split("\n")[-3:]:
            # Find the last decorator line
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if f"async def {func_name}" in line:
                    # Find where to insert the marker
                    marker_pos = i
                    while marker_pos > 0 and "@pytest.mark." in lines[marker_pos - 1]:
                        marker_pos -= 1

                    # Insert the asyncio marker
                    indent_match = re.match(r"(\s*)", lines[marker_pos])
                    indent = indent_match.group(1) if indent_match else "    "
                    lines.insert(marker_pos, f"{indent}@pytest.mark.asyncio")
                    added_markers += 1
                    break

            # Reconstruct the content
            content = "\n".join(lines)

    return content, added_markers


def process_file(file_path: str) -> tuple[int, int, set[str], int] | None:
    """Process a single file and fix all issues."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"Could not decode {file_path} as UTF-8, skipping...")
        return None
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

    # Skip empty files
    if not content.strip():
        return None

    original_content = content

    # Fix duplicate markers
    content, duplicate_fixes = fix_duplicate_markers(content)

    # Fix indentation issues
    content, indentation_fixes = fix_indentation_issues(content)

    # Add async to functions
    content, fixed_functions = add_async_to_functions(content)

    # Ensure async functions have asyncio marker
    content, added_markers = ensure_asyncio_marker(content, fixed_functions)

    # Write back only if changes were made
    if content != original_content:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return duplicate_fixes, indentation_fixes, fixed_functions, added_markers
        except Exception as e:
            print(f"Error writing to {file_path}: {e}")
            return None

    return 0, 0, set(), 0


def main():
    """Main entry point."""
    # Get the base directory
    base_dir = Path(__file__).parent

    # Check if a target directory was specified
    target_dir = sys.argv[1] if len(sys.argv) > 1 else None

    # Find all test files
    test_files = find_test_files(base_dir, target_dir)
    print(
        f"Found {len(test_files)} test files"
        + (f" in {target_dir}" if target_dir else "")
    )

    # Process each file
    total_files_fixed = 0
    total_duplicate_fixes = 0
    total_indentation_fixes = 0
    total_functions_fixed = 0
    total_markers_added = 0

    for file_path in test_files:
        result = process_file(file_path)
        if result:
            duplicate_fixes, indentation_fixes, fixed_functions, added_markers = result
            if duplicate_fixes or indentation_fixes or fixed_functions or added_markers:
                total_files_fixed += 1
                total_duplicate_fixes += duplicate_fixes
                total_indentation_fixes += indentation_fixes
                total_functions_fixed += len(fixed_functions)
                total_markers_added += added_markers

                # Print details of fixes
                changes = []
                if duplicate_fixes:
                    changes.append(f"{duplicate_fixes} duplicate markers")
                if indentation_fixes:
                    changes.append(f"{indentation_fixes} indentation issues")
                if fixed_functions:
                    functions_str = ", ".join(fixed_functions)
                    changes.append(
                        f"added async to {len(fixed_functions)} functions: {functions_str}"
                    )
                if added_markers:
                    changes.append(f"added {added_markers} asyncio markers")

                print(f"Fixed in {file_path}:\n  - " + "\n  - ".join(changes))

    print("\nSummary:")
    print(f"- Fixed issues in {total_files_fixed} files")
    print(f"- Removed {total_duplicate_fixes} duplicate markers")
    print(f"- Fixed {total_indentation_fixes} indentation issues")
    print(f"- Added 'async' keyword to {total_functions_fixed} functions")
    print(f"- Added {total_markers_added} missing asyncio markers")
    print(f"- {len(test_files) - total_files_fixed} files were already correct")


if __name__ == "__main__":
    sys.exit(main())
