#!/usr/bin/env python3
"""
Comprehensive script to fix all test file issues:
1. Replace duplicate 'async async def' with 'async def'
2. Fix broken pytest markers like @pytest.mark.[a-z]+ with @pytest.mark.unit
3. Ensure proper formatting of test files
"""

import os
import re
from pathlib import Path


def fix_file(file_path: Path) -> tuple[bool, list[str]]:
    """
    Fix issues in a test file.

    Args:
        file_path: Path to the file to fix

    Returns:
        tuple: (was_modified, list_of_changes_made)
    """
    changes = []
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Fix 1: Replace duplicate async keywords
        if re.search(r"async\s+async\s+def", content):
            content = re.sub(r"async\s+async\s+def", "async def", content)
            changes.append("Fixed duplicate async keywords")

        # Process line by line for precise marker fixes
        lines = content.split("\n")
        for i, line in enumerate(lines):
            # Fix literal @pytest.mark.[a-z]+ markers
            if "@pytest.mark.[a-z]+" in line:
                lines[i] = line.replace("@pytest.mark.[a-z]+", "@pytest.mark.unit")
                changes.append(f"Fixed literal marker: {line} -> {lines[i]}")

            # Fix actual regex pattern @pytest.mark.\[a-z\]+
            elif re.search(r"@pytest\.mark\.\[a-z\]\+", line):
                lines[i] = re.sub(
                    r"@pytest\.mark\.\[a-z\]\+", "@pytest.mark.unit", line
                )
                changes.append(f"Fixed regex marker: {line} -> {lines[i]}")

            # Fix any other problematic markers with square brackets
            elif "@pytest.mark." in line and "[" in line and "]" in line:
                # This handles cases where the marker got corrupted in other ways
                match = re.search(r"@pytest\.mark\.(\[[^\]]*\])", line)
                if match:
                    corrupted_part = match.group(1)
                    lines[i] = line.replace(
                        f"@pytest.mark.{corrupted_part}", "@pytest.mark.unit"
                    )
                    changes.append(f"Fixed bracketed marker: {line} -> {lines[i]}")

        # Join the lines back into content
        new_content = "\n".join(lines)

        # If we changed the content, update it
        if new_content != content:
            content = new_content

        # If no changes were made to the original content, return False
        if content == original_content:
            return False, []

        # Write the modified content back to the file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return True, changes

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False, [f"Error: {str(e)}"]


def main():
    """Main function to scan and fix all Python files in the tests directory."""
    tests_dir = Path(__file__).parent / "tests"
    print(f"Scanning for Python files in {tests_dir}")

    files_fixed = 0
    total_files = 0
    all_changes = {}

    # Walk through all Python files in the tests directory
    for root, _, files in os.walk(tests_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                total_files += 1

                was_modified, changes = fix_file(file_path)
                if was_modified:
                    files_fixed += 1
                    all_changes[str(file_path)] = changes
                    print(f"Fixed: {file_path}")
                    for change in changes:
                        print(f"  - {change}")

    print("\nSummary:")
    print(f"Total Python files scanned: {total_files}")
    print(f"Files fixed: {files_fixed}")

    if files_fixed > 0:
        print("\nDetailed changes:")
        for file_path, changes in all_changes.items():
            print(f"\n{file_path}:")
            for change in changes:
                print(f"  - {change}")


if __name__ == "__main__":
    main()
