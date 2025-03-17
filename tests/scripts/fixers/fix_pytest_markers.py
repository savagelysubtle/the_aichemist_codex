#!/usr/bin/env python
"""
Script to fix invalid pytest markers in test files.

This script replaces placeholder pytest markers like '@pytest.mark.[a-z]+' with
proper pytest markers like '@pytest.mark.unit'.
"""

import os
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


def fix_markers(file_path: Path) -> tuple[bool, int]:
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
        markers_fixed = 0

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


def main():
    """Main function to find and fix test files."""
    # Get the project root directory
    project_root = Path(__file__).resolve().parent.parent
    tests_dir = project_root / "tests"

    print(f"Searching for test files in {tests_dir}...")
    test_files = find_test_files(tests_dir)
    print(f"Found {len(test_files)} test files")

    total_files_fixed = 0
    total_markers_fixed = 0

    for file_path in test_files:
        modified, markers_fixed = fix_markers(file_path)
        if modified:
            total_files_fixed += 1
            total_markers_fixed += markers_fixed
            print(f"Fixed {markers_fixed} markers in {file_path}")

    print("\nSummary:")
    print(f"- Files fixed: {total_files_fixed}")
    print(f"- Markers fixed: {total_markers_fixed}")


if __name__ == "__main__":
    main()
