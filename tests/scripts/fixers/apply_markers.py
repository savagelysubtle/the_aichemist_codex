"""
Script to add appropriate pytest markers to test files based on their categories.
"""

import re
from pathlib import Path

# Path to the unit tests directory
unit_dir = Path("backend/tests/unit")

# Mapping of directories to markers
directory_markers = {
    "cli": ["cli", "unit"],
    "utils": ["unit"],
    "core": ["unit"],
    "tagging": ["tagging", "unit"],
    "search": ["search", "unit"],
    "ingest": ["unit"],
    "relationships": ["unit"],
    "file_operations": ["unit"],
    "output": ["unit"],
    "content_processing": ["unit"],
    "metadata": ["metadata", "unit"],
}


# Function to add markers to test functions in a file
def add_markers_to_file(file_path, markers):
    print(f"Processing {file_path}...")

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Find test functions
    test_function_pattern = r"def\s+(test_\w+)"
    test_functions = re.findall(test_function_pattern, content)

    if not test_functions:
        print(f"  No test functions found in {file_path}")
        return

    for test_func in test_functions:
        # Create marker decorators
        marker_lines = [f"@pytest.mark.{marker}" for marker in markers]
        markers_text = "\n".join(marker_lines)

        # Check if the function already has these markers
        func_with_context = f"def {test_func}"
        if any(
            f"@pytest.mark.{marker}"
            in content.split(func_with_context)[0].split("def ")[-1]
            for marker in markers
        ):
            print(f"  {test_func} already has markers, skipping")
            continue

        # Replace the function definition with markers + function definition
        replacement = f"{markers_text}\ndef {test_func}"
        content = content.replace(f"def {test_func}", replacement)

    # Write back to the file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  Updated {len(test_functions)} test functions in {file_path}")


# Process each directory
for category, markers in directory_markers.items():
    category_dir = unit_dir / category
    if not category_dir.exists():
        print(f"Directory {category_dir} does not exist, skipping")
        continue

    print(f"\nProcessing directory: {category}")

    # Find all test files in the directory
    for file_path in category_dir.glob("test_*.py"):
        # Check if pytest is imported
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Add pytest import if needed
        if "import pytest" not in content:
            content = "import pytest\n" + content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  Added pytest import to {file_path}")

        # Add markers
        add_markers_to_file(file_path, markers)

print("\nMarker application complete!")
