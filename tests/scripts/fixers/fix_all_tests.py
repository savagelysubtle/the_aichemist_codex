#!/usr/bin/env python
"""
Comprehensive script to fix all test issues.

This script combines multiple fixes:
1. Fixes invalid pytest markers (@pytest.mark.[a-z]+)
2. Fixes async test syntax
3. Ensures proper imports

Run this script from the project root:
    python tests/fix_all_tests.py
"""

import os
import re
import subprocess
import sys
from pathlib import Path


def find_test_files(base_dir: Path) -> list[Path]:
    """Find all Python test files in the given directory and subdirectories."""
    test_files = []

    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                file_path = Path(root) / file
                test_files.append(file_path)

    return test_files


def fix_pytest_markers(file_path: Path) -> tuple[bool, int]:
    """
    Fix invalid pytest markers in the given file.

    Args:
        file_path: Path to the file to fix

    Returns:
        tuple: (whether file was modified, number of markers fixed)
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Check if the file has the invalid marker pattern
        if "@pytest.mark.[a-z]+" not in content:
            return False, 0

        # Replace the invalid markers with appropriate ones based on the file path
        # Determine which marker to use based on directory name
        if "unit" in str(file_path):
            replacement = "@pytest.mark.unit"
        elif "integration" in str(file_path):
            replacement = "@pytest.mark.integration"
        else:
            replacement = "@pytest.mark.unit"  # Default to unit if unclear

        # Specific markers based on directory
        if "metadata" in str(file_path):
            content = content.replace(
                "@pytest.mark.[a-z]+\n@pytest.mark.metadata",
                "@pytest.mark.unit\n@pytest.mark.metadata",
            )
            content = content.replace("@pytest.mark.[a-z]+", "@pytest.mark.metadata")
        elif "cli" in str(file_path):
            content = content.replace("@pytest.mark.[a-z]+", "@pytest.mark.cli")
        elif "core" in str(file_path):
            content = content.replace("@pytest.mark.[a-z]+", "@pytest.mark.unit")
        elif "file_operations" in str(file_path):
            content = content.replace("@pytest.mark.[a-z]+", "@pytest.mark.unit")
        elif "ingest" in str(file_path):
            content = content.replace("@pytest.mark.[a-z]+", "@pytest.mark.ingest")
        elif "search" in str(file_path):
            content = content.replace("@pytest.mark.[a-z]+", "@pytest.mark.search")
        elif "tagging" in str(file_path):
            content = content.replace("@pytest.mark.[a-z]+", "@pytest.mark.tagging")
        elif "content_processing" in str(file_path):
            content = content.replace("@pytest.mark.[a-z]+", "@pytest.mark.unit")
        else:
            content = content.replace("@pytest.mark.[a-z]+", replacement)

        # Count the number of replacements
        markers_fixed = content.count("@pytest.mark") - content.count(
            "@pytest.mark.[a-z]+"
        )

        # Write the fixed content back to the file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return True, markers_fixed

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False, 0


def fix_async_test_syntax(file_path: Path) -> tuple[bool, int, int]:
    """
    Fix async test syntax in the given file.

    Args:
        file_path: Path to the file to fix

    Returns:
        tuple: (whether file was modified, duplicate fixes, missing async fixes)
    """
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
    missing_async = re.search(r"def\s+test_\w+.*\n.*?\s+await\s+", content, re.DOTALL)

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
        # Find all test functions that use await but don't have async
        pattern = r"(def\s+test_\w+.*?\(.*?\).*?:)(?:.*?\n)+?(?:.*?await)"
        matches = re.finditer(pattern, content, re.DOTALL)

        # Keep track of functions already processed to avoid duplication
        processed_funcs = set()

        for match in matches:
            func_def = match.group(1)
            # Extract function name
            func_name_match = re.search(r"def\s+(test_\w+)", func_def)
            if not func_name_match:
                continue

            func_name = func_name_match.group(1)

            if func_name in processed_funcs:
                continue

            processed_funcs.add(func_name)

            if "async def" not in func_def:
                # Replace the function definition with 'async def'
                new_func_def = func_def.replace("def ", "async def ", 1)
                content = content.replace(func_def, new_func_def)

                # Also ensure it has the asyncio marker
                # Find the functions with their decorators
                func_with_decorators = re.search(
                    r"((?:@pytest\.mark\.\w+\s+)*)" + re.escape(new_func_def), content
                )

                if (
                    func_with_decorators
                    and "@pytest.mark.asyncio" not in func_with_decorators.group(1)
                ):
                    # Add asyncio marker before the function
                    decorators = func_with_decorators.group(1)
                    # Get indentation
                    indent_match = re.search(r"^(\s*)", new_func_def)
                    indent = indent_match.group(1) if indent_match else "    "

                    new_decorated_func = (
                        f"{decorators}{indent}@pytest.mark.asyncio\n{new_func_def}"
                    )
                    content = content.replace(
                        f"{decorators}{new_func_def}", new_decorated_func
                    )

                missing_async_fixes += 1

    # Write the fixed content back to the file
    if duplicate_fixes > 0 or missing_async_fixes > 0:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    return True, duplicate_fixes, missing_async_fixes


def install_dependencies():
    """Install missing dependencies needed for tests."""
    print("Installing missing dependencies...")

    # List of dependencies that might be missing based on test errors
    dependencies = [
        "mutagen",  # For audio file metadata extraction
        "pytest",
        "pytest-asyncio",
        "pytest-cov",
        "pytest-mock",
        "scipy",
        "numpy",
        "pydub",
    ]

    # Install each dependency
    installed_count = 0
    failed_count = 0

    for package in dependencies:
        try:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            installed_count += 1
        except subprocess.CalledProcessError as e:
            print(f"Error installing {package}: {e}")
            failed_count += 1

    print(f"\nInstalled {installed_count} packages.")
    if failed_count > 0:
        print(f"Failed to install {failed_count} packages.")


def main():
    """Main function to fix all test issues."""
    # Get the project root directory
    project_root = Path(__file__).resolve().parent.parent
    tests_dir = project_root / "tests"

    # Step 1: Install missing dependencies
    print("Step 1: Installing missing dependencies...")
    install_dependencies()

    # Step 2: Fix pytest markers
    print("\nStep 2: Fixing invalid pytest markers...")
    test_files = find_test_files(tests_dir)
    print(f"Found {len(test_files)} test files")

    marker_fixes_count = 0
    async_fixes_count = 0
    missing_async_count = 0
    total_files_fixed = 0

    for file_path in test_files:
        # Fix markers
        marker_fixed, markers_count = fix_pytest_markers(file_path)

        # Fix async syntax
        async_fixed, duplicate_count, missing_async = fix_async_test_syntax(file_path)

        if marker_fixed or async_fixed:
            total_files_fixed += 1
            marker_fixes_count += markers_count
            async_fixes_count += duplicate_count
            missing_async_count += missing_async

            changes = []
            if markers_count > 0:
                changes.append(f"{markers_count} markers")
            if duplicate_count > 0:
                changes.append(f"{duplicate_count} duplicate asyncio markers")
            if missing_async > 0:
                changes.append(f"{missing_async} missing 'async' keywords")

            if changes:
                print(f"Fixed {', '.join(changes)} in {file_path}")

    # Print summary
    print("\nSummary:")
    print(f"- Files fixed: {total_files_fixed}")
    print(f"- Invalid markers fixed: {marker_fixes_count}")
    print(f"- Duplicate asyncio markers removed: {async_fixes_count}")
    print(f"- Missing 'async' keywords added: {missing_async_count}")


if __name__ == "__main__":
    main()
