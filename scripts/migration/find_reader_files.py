"""
File Reader Directory Explorer
- Lists all files in the file_reader directory
- Creates a migration plan for those files
"""

import json
import os

PROJECT_ROOT = r"D:\Coding\Python_Projects\the_aichemist_codex"
FILE_READER_DIR = os.path.join(
    PROJECT_ROOT, "src", "the_aichemist_codex", "backend", "core", "file_reader"
)

# Dictionary to store files by category
files_by_category = {}

print(f"Examining file_reader directory: {FILE_READER_DIR}\n")

if os.path.exists(FILE_READER_DIR):
    # Get all Python files in directory
    python_files = []
    for file in os.listdir(FILE_READER_DIR):
        if file.endswith(".py"):
            full_path = os.path.join(FILE_READER_DIR, file)
            rel_path = os.path.relpath(full_path, PROJECT_ROOT).replace("/", "\\")
            python_files.append((file, rel_path))

    print(f"Found {len(python_files)} Python files in file_reader directory:")
    for file, path in python_files:
        print(f"- {file} (Path: {path})")

    # Create migration plan based on file names
    migration_plan = []
    for file, path in python_files:
        # Determine target directory based on file name
        if "metadata" in file.lower():
            category = "filesystem"
        elif "ocr" in file.lower():
            category = "parsing"
        elif "reader" in file.lower():
            category = "filesystem"
        elif "parser" in file.lower() or "parse" in file.lower():
            category = "parsing"
        else:
            category = "filesystem"  # Default category

        # Store by category for better organization
        if category not in files_by_category:
            files_by_category[category] = []
        files_by_category[category].append((file, path))

        # Create migration entry
        destination = f"src\\the_aichemist_codex\\core\\{category}\\{file}"
        migration_plan.append(
            {
                "source": path,
                "destination": destination,
                "imports_to_update": {
                    "from .. import": "from the_aichemist_codex.core import",
                    "from ..": "from the_aichemist_codex.core.",
                    "from .": "from the_aichemist_codex.core." + category + ".",
                },
            }
        )

    # Save migration plan to file
    with open(
        os.path.join(os.path.dirname(__file__), "reader_migration_plan.json"), "w"
    ) as f:
        json.dump(migration_plan, f, indent=2)

    print("\nCreated migration plan for file_reader files.")
    print("Plan saved to: reader_migration_plan.json")

    # Print files by category
    print("\nFiles organized by target category:")
    for category, files in files_by_category.items():
        print(f"\n{category.upper()}:")
        for file, path in files:
            print(f"- {file}")
else:
    print(f"Error: Directory not found: {FILE_READER_DIR}")

input("\nPress Enter to exit...")
