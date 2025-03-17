#!/usr/bin/env python3
"""
Optimized script to fix pytest marker issues in test files.
This version uses multiprocessing to speed up execution.
"""

import multiprocessing
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path


def fix_file(file_path: Path) -> tuple[bool, int, str]:
    """
    Fix a file by replacing '@pytest.mark.[a-z]+' with '@pytest.mark.unit'.

    Args:
        file_path: Path to the file to fix

    Returns:
        tuple: (was_modified, number_of_replacements, file_path)
    """
    try:
        # Quick check first - if the file doesn't contain the string, skip full processing
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            # Read the first few KB to check if the marker pattern might be present
            first_chunk = f.read(4096)
            if "@pytest.mark.[a-z]+" not in first_chunk:
                # Quick preliminary check for common pattern - if not found in first chunk,
                # read the rest of the file only if necessary
                if "pytest.mark" not in first_chunk:
                    return False, 0, str(file_path)

                # Read the rest of the file to check more thoroughly
                rest_of_file = f.read()
                if "@pytest.mark.[a-z]+" not in rest_of_file:
                    return False, 0, str(file_path)

                # Pattern found in rest of file, process the entire file
                content = first_chunk + rest_of_file
            else:
                # Pattern found in first chunk, read the rest and process
                content = first_chunk + f.read()

        # Count the occurrences
        count = content.count("@pytest.mark.[a-z]+")

        # If no occurrences, return early
        if count == 0:
            return False, 0, str(file_path)

        # Replace the literal pattern
        modified_content = content.replace("@pytest.mark.[a-z]+", "@pytest.mark.unit")

        # Write to the file if changes were made
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(modified_content)

        return True, count, str(file_path)

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False, 0, str(file_path)


def find_python_files(directory: Path) -> list[Path]:
    """Find all Python files in the given directory recursively."""
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)
    return python_files


def main():
    """Main function to fix all files with marker issues using multiprocessing."""
    tests_dir = Path(__file__).parent / "tests"
    print(f"Scanning for Python files in {tests_dir}")

    # Get all Python files
    python_files = find_python_files(tests_dir)
    total_files = len(python_files)
    print(f"Found {total_files} Python files to process")

    # Use the number of CPU cores for parallel processing
    num_processors = multiprocessing.cpu_count()
    print(f"Using {num_processors} processors for parallel execution")

    files_fixed = 0
    total_replacements = 0

    # Process files in parallel
    with ProcessPoolExecutor(max_workers=num_processors) as executor:
        # Submit all file processing tasks
        future_to_file = {
            executor.submit(fix_file, file_path): file_path
            for file_path in python_files
        }

        # Process results as they complete
        for future in as_completed(future_to_file):
            was_modified, replacements, file_path = future.result()
            if was_modified:
                files_fixed += 1
                total_replacements += replacements
                print(f"Fixed: {file_path} - {replacements} replacements")

    print("\nSummary:")
    print(f"Total Python files scanned: {total_files}")
    print(f"Files fixed: {files_fixed}")
    print(f"Total replacements: {total_replacements}")


if __name__ == "__main__":
    main()
