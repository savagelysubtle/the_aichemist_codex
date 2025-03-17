#!/usr/bin/env python3
"""
Script to clean up documentation files in the root directory.

This script:
1. Identifies documentation files in the root directory
2. Copies them to the docs directory if they don't already exist there
3. Creates a backup of the original files
4. Replaces the original with a redirect to the docs directory

Usage:
  python scripts/cleanup_docs.py
"""

import re
import shutil
from pathlib import Path

# Path setup
ROOT_DIR = Path(__file__).parent.parent
DOCS_DIR = ROOT_DIR / "docs"
BACKUP_DIR = ROOT_DIR / "backup" / "docs_cleanup"

# Documentation file patterns
DOC_PATTERNS = [
    r".*\.md$",  # Markdown files
    r".*\.rst$",  # ReStructuredText files
    r".*\.txt$",  # Text files that might be documentation
    r"^[Dd][Oo][Cc][Ss]?.*$",  # Files starting with "doc" or "docs"
    r".*[Dd]ocumentation.*$",  # Files with "documentation" in the name
]

# Files to exclude (files that should stay in the root)
EXCLUDE_FILES = {
    "README.md",  # Main README should stay in root
    ".gitignore",
    "pyproject.toml",
    "Makefile",
    "LICENSE",
    "CHANGELOG.md",  # If you prefer to keep this in the root
}

# Placeholder content for the root docs README
ROOT_DOCS_README = """# Documentation

Documentation has been moved to the `docs/` directory.
Please see the docs directory for the current documentation.
"""


def is_doc_file(file_path: Path) -> bool:
    """Check if a file is likely a documentation file."""
    if file_path.name in EXCLUDE_FILES:
        return False

    for pattern in DOC_PATTERNS:
        if re.match(pattern, file_path.name):
            return True

    return False


def main():
    """Run the documentation cleanup process."""
    print(f"Scanning {ROOT_DIR} for documentation files...")

    # Ensure backup directory exists
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # Get list of root files
    root_files = [f for f in ROOT_DIR.iterdir() if f.is_file()]
    doc_files = [f for f in root_files if is_doc_file(f)]

    if not doc_files:
        print("No documentation files found in the root directory.")
        return

    print(f"Found {len(doc_files)} potential documentation files:")
    for doc_file in doc_files:
        print(f"  - {doc_file.name}")

    # Process each file
    for doc_file in doc_files:
        # Create destination path in docs directory
        dest_path = DOCS_DIR / doc_file.name.lower().replace(" ", "_")

        # Create backup
        backup_path = BACKUP_DIR / doc_file.name
        print(f"Backing up {doc_file.name} to {backup_path}")
        shutil.copy2(doc_file, backup_path)

        # Check if the file already exists in docs
        if dest_path.exists():
            print(f"File already exists in docs directory: {dest_path}")
        else:
            # Copy to docs directory with normalized name
            print(f"Copying {doc_file.name} to {dest_path}")
            shutil.copy2(doc_file, dest_path)

        # Replace the original with a redirect README
        print(f"Replacing {doc_file.name} with redirect notice")
        doc_file.unlink()

    # Create the root docs README if it doesn't exist
    root_docs_readme_path = ROOT_DIR / "DOCUMENTATION.md"
    if not root_docs_readme_path.exists():
        print("Creating DOCUMENTATION.md in root directory")
        root_docs_readme_path.write_text(ROOT_DOCS_README)

    print("\nDocumentation cleanup complete. Files have been:")
    print(f"1. Backed up to {BACKUP_DIR}")
    print(f"2. Copied to {DOCS_DIR} (if they didn't already exist)")
    print("3. Removed from the root directory")
    print("4. A DOCUMENTATION.md file has been created in the root")


if __name__ == "__main__":
    main()
