#!/usr/bin/env python3
"""
Documentation Structure Fixer

This script scans the documentation directory for files that break organization rules
and automatically moves them to their proper locations based on content analysis.

Usage:
    python fix_documentation_structure.py [--dry-run] [--verbose]
"""

import argparse
import logging
import os
import re
import shutil
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("doc_fixer")


# Define the project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = PROJECT_ROOT / "docs"


# Documentation organization rules
DOCUMENTATION_RULES = {
    "allowed_extensions": {".rst"},
    "discouraged_extensions": {".md"},
    "directories": {
        "api": {
            "path": DOCS_ROOT / "api",
            "description": "API reference documentation",
            "patterns": [
                r".*_api\.rst$",
                r"api\.rst$",
                r"endpoints\.rst$",
                r"rest_.*\.rst$",
                r"graphql_.*\.rst$",
            ],
            "keywords": ["api", "endpoint", "rest", "graphql", "interface"],
        },
        "architecture": {
            "path": DOCS_ROOT / "architecture",
            "description": "Architecture documentation and diagrams",
            "patterns": [
                r".*_layer\.rst$",
                r"architecture.*\.rst$",
                r"design.*\.rst$",
                r".*_pattern\.rst$",
                r"overview\.rst$",
                r"structure\.rst$",
            ],
            "keywords": ["architecture", "layer", "pattern", "design", "structure"],
        },
        "guides": {
            "path": DOCS_ROOT / "guides",
            "description": "User and developer guides",
            "patterns": [
                r"installation\.rst$",
                r"configuration\.rst$",
                r"user.*guide\.rst$",
                r"admin.*guide\.rst$",
                r"developer.*guide\.rst$",
                r"troubleshooting\.rst$",
                r"how_to_.*\.rst$",
                r"contributing\.rst$",
                r"code_style\.rst$",
            ],
            "keywords": [
                "guide",
                "installation",
                "configuration",
                "troubleshoot",
                "setup",
                "how to",
                "contributing",
                "code style",
            ],
        },
        "tutorials": {
            "path": DOCS_ROOT / "tutorials",
            "description": "Tutorial content and examples",
            "patterns": [
                r"tutorial.*\.rst$",
                r"getting_started\.rst$",
                r"quickstart\.rst$",
                r"example.*\.rst$",
                r"advanced_usage\.rst$",
                r"search_techniques\.rst$",
                r"semantic_search\.rst$",
                r"quick_start\.rst$",
                r"file_organization\.rst$",
            ],
            "keywords": [
                "tutorial",
                "getting started",
                "quickstart",
                "example",
                "usage",
            ],
        },
        "diagrams": {
            "path": DOCS_ROOT / "diagrams",
            "description": "Diagram files (images, source files)",
            "patterns": [],  # Usually image files, not matched by patterns
            "keywords": ["diagram", "chart", "figure"],
        },
        "roadmap": {
            "path": DOCS_ROOT / "roadmap",
            "description": "Project roadmap and future plans",
            "patterns": [
                r"roadmap\.rst$",
                r"vision\.rst$",
                r"future.*\.rst$",
                r"planned.*\.rst$",
                r"milestones\.rst$",
            ],
            "keywords": ["roadmap", "vision", "future", "plan", "milestone"],
        },
        "images": {
            "path": DOCS_ROOT / "images",
            "description": "Documentation images and screenshots",
            "patterns": [],  # Image files, not matched by patterns
            "keywords": ["image", "screenshot", "picture"],
        },
    },
    "ignored_dirs": {"scripts", "_build", "_static", "_templates"},
    "root_files": {
        "index.rst",
        "conf.py",
        "make.bat",
        "Makefile",
        "requirements.txt",
        "README.rst",
        "README.md",  # Allow README.md to stay in root, we'll convert it if needed
        ".gitignore",
        "environment.yml",
        "tox.ini",
        "setup.py",
    },
    # Files with their correct categorization
    "specific_file_mappings": {
        "contributing.rst": "guides",
        "code_style.rst": "guides",
        "changelog.rst": "root",  # Keep changelog in root
        "usage.rst": "guides",
        "cli_reference.rst": "guides",
    },
    # Preserve hierarchy for these file patterns
    "preserve_hierarchy": [
        r"index\.rst$",  # Preserve directory structure for index files
        r"^_.*\.rst$",  # Files starting with underscore are often special
    ],
}


def ensure_directories_exist() -> None:
    """Ensure all documentation directories exist."""
    for dir_config in DOCUMENTATION_RULES["directories"].values():
        dir_path = dir_config["path"]
        if not dir_path.exists():
            logger.info(f"Creating missing directory: {dir_path}")
            dir_path.mkdir(parents=True, exist_ok=True)


def get_all_doc_files() -> list[Path]:
    """Scan the docs directory and return all documentation files."""
    all_files = []
    for root, dirs, files in os.walk(DOCS_ROOT):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if d not in DOCUMENTATION_RULES["ignored_dirs"]]

        for file in files:
            file_path = Path(root) / file
            all_files.append(file_path)

    return all_files


def analyze_file_content(file_path: Path) -> str | None:
    """
    Analyze file content to determine its category.
    Returns the appropriate directory key where the file should belong,
    or None if it can't be categorized.
    """
    # Check for specific file mappings first
    filename = file_path.name
    if filename in DOCUMENTATION_RULES["specific_file_mappings"]:
        category = DOCUMENTATION_RULES["specific_file_mappings"][filename]
        if category == "root":
            return None  # Keep in root directory
        return category

    # Next check the file extension and name patterns
    for dir_key, dir_config in DOCUMENTATION_RULES["directories"].items():
        for pattern in dir_config["patterns"]:
            if re.search(pattern, file_path.name, re.IGNORECASE):
                return dir_key

    # If no match by filename, try to determine by content
    try:
        content = file_path.read_text(encoding="utf-8")

        # Check for keywords in the content
        for dir_key, dir_config in DOCUMENTATION_RULES["directories"].items():
            if "keywords" in dir_config:
                if any(kw in content.lower() for kw in dir_config["keywords"]):
                    return dir_key
    except Exception as e:
        logger.warning(f"Could not analyze content of {file_path}: {str(e)}")

    # Check if it should preserve hierarchy
    for pattern in DOCUMENTATION_RULES["preserve_hierarchy"]:
        if re.search(pattern, file_path.name):
            # For index.rst and special files, keep them in their original location
            # or in the parent directory category
            parent_dir = file_path.parent.name
            if parent_dir in DOCUMENTATION_RULES["directories"]:
                return parent_dir
            # If parent is not a known category but grandparent is
            if len(file_path.parts) > 3:  # We need at least docs/category/subdir
                grandparent = file_path.parts[-3]
                if grandparent in DOCUMENTATION_RULES["directories"]:
                    return grandparent

    # Default: keep in current location if it's already in a valid directory
    parent_dir = file_path.parent.name
    if parent_dir in DOCUMENTATION_RULES["directories"]:
        return parent_dir

    # For files in specific subdirectories, preserve their context
    if parent_dir and any(
        parent_dir.lower() in dir_config.get("keywords", [])
        for dir_config in DOCUMENTATION_RULES["directories"].values()
    ):
        # Try to find the appropriate category based on parent directory name
        for dir_key, dir_config in DOCUMENTATION_RULES["directories"].items():
            if parent_dir.lower() in dir_config.get("keywords", []):
                return dir_key

    # Default to architecture for .rst files that couldn't be categorized
    if file_path.suffix.lower() == ".rst":
        # Use guides as a default for files in the root
        if file_path.parent == DOCS_ROOT:
            return "guides"
        return "architecture"

    # Images go to images directory
    if file_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".svg"}:
        return "images"

    # For all other files, return None (indicating no action)
    return None


def convert_md_to_rst(md_file: Path) -> Path | None:
    """
    Convert a markdown file to reStructuredText.
    Returns the path to the new .rst file, or None if conversion fails.
    """
    try:
        # Check if pandoc is installed
        import subprocess

        rst_file = md_file.with_suffix(".rst")
        logger.info(f"Converting {md_file} to {rst_file}")

        result = subprocess.run(
            ["pandoc", str(md_file), "-o", str(rst_file)],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            logger.error(f"Pandoc conversion failed: {result.stderr}")
            return None

        return rst_file

    except (ImportError, FileNotFoundError):
        logger.warning(
            "Pandoc not found. Cannot convert Markdown to RST. Please install pandoc."
        )
        return None


def should_move_file(file_path: Path) -> bool:
    """Determine if a file should be moved based on our rules."""
    # Skip files in ignored directories
    for ignored in DOCUMENTATION_RULES["ignored_dirs"]:
        if ignored in file_path.parts:
            return False

    # Files with incorrect extensions should be moved/converted
    if file_path.suffix.lower() in DOCUMENTATION_RULES["discouraged_extensions"]:
        # Except for those in root_files
        if file_path.name in DOCUMENTATION_RULES["root_files"]:
            # README.md should be converted but kept in root
            if file_path.name == "README.md" and file_path.parent == DOCS_ROOT:
                return True
            return False
        return True

    # Only process documentation files
    if file_path.suffix.lower() not in DOCUMENTATION_RULES["allowed_extensions"]:
        # Allow image files
        image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".svg"}
        if file_path.suffix.lower() not in image_extensions:
            return False

    # Check if file is in the docs root but should be in a subdirectory
    if file_path.parent == DOCS_ROOT:
        # Files that should stay in the root
        if file_path.name in DOCUMENTATION_RULES["root_files"]:
            return False
        # Check specific file mappings
        if file_path.name in DOCUMENTATION_RULES["specific_file_mappings"]:
            if DOCUMENTATION_RULES["specific_file_mappings"][file_path.name] == "root":
                return False
        return True

    # For index.rst files, check if they should be preserved in their location
    if file_path.name == "index.rst":
        # If in a valid category directory, don't move
        if file_path.parent.name in DOCUMENTATION_RULES["directories"]:
            return False
        # If parent dir gives context, preserve it in the filename when moved
        return True

    # Determine if file is in the correct directory based on its content
    target_dir = analyze_file_content(file_path)
    if (
        target_dir
        and DOCUMENTATION_RULES["directories"][target_dir]["path"] != file_path.parent
    ):
        return True

    return False


def get_target_location(file_path: Path) -> tuple[Path | None, bool]:
    """
    Determine the target location for a file.
    Returns a tuple of (target_path, needs_conversion).
    """
    # If it's a markdown file, we need to convert it
    needs_conversion = (
        file_path.suffix.lower() in DOCUMENTATION_RULES["discouraged_extensions"]
    )

    # Special case for README.md in root - convert but keep in root
    if file_path.name == "README.md" and file_path.parent == DOCS_ROOT:
        if needs_conversion:
            return DOCS_ROOT / "README.rst", needs_conversion
        return None, needs_conversion

    # Determine the target directory
    target_dir_key = analyze_file_content(file_path)
    if not target_dir_key:
        return None, needs_conversion

    target_dir = DOCUMENTATION_RULES["directories"][target_dir_key]["path"]

    # Handle index files - preserve hierarchy information in filename
    if file_path.name == "index.rst" and file_path.parent != DOCS_ROOT:
        # Get the parent directory name to include in the new filename
        parent_name = file_path.parent.name
        # Construct a new name like "parent_index.rst"
        if needs_conversion:
            target_name = f"{parent_name}_index.rst"
        else:
            target_name = f"{parent_name}_index.rst"
    else:
        # For other files, check if we need to preserve directory context
        for pattern in DOCUMENTATION_RULES["preserve_hierarchy"]:
            if re.search(pattern, file_path.name):
                # Get the parent directory name to include in the new filename
                parent_name = file_path.parent.name
                if (
                    parent_name != "docs"
                    and parent_name not in DOCUMENTATION_RULES["directories"]
                ):
                    # Construct a new name like "parent_filename.rst"
                    if needs_conversion:
                        target_name = f"{parent_name}_{file_path.stem}.rst"
                    else:
                        target_name = f"{parent_name}_{file_path.name}"
                    break
        else:
            # Regular files
            if needs_conversion:
                target_name = file_path.stem + ".rst"
            else:
                target_name = file_path.name

    target_path = target_dir / target_name

    # Handle name collisions
    counter = 1
    original_stem = Path(target_name).stem
    original_suffix = Path(target_name).suffix
    while target_path.exists():
        target_name = f"{original_stem}_{counter}{original_suffix}"
        target_path = target_dir / target_name
        counter += 1

    return target_path, needs_conversion


def move_file(file_path: Path, target_path: Path, dry_run: bool = False) -> bool:
    """Move a file to its target location."""
    try:
        logger.info(f"Moving {file_path} to {target_path}")
        if not dry_run:
            # Make sure target directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Move the file
            shutil.move(str(file_path), str(target_path))
        return True
    except Exception as e:
        logger.error(f"Error moving file {file_path}: {str(e)}")
        return False


def update_index_files(changes: list[tuple[Path, Path]], dry_run: bool = False) -> None:
    """Update index files to reference moved files."""
    # Group changes by directory
    dirs_to_update = set()
    for _, target_path in changes:
        dirs_to_update.add(target_path.parent)

    for dir_path in dirs_to_update:
        index_path = dir_path / "index.rst"

        # Create index file if it doesn't exist
        if not index_path.exists() and not dry_run:
            # Get directory name from the path
            dir_name = dir_path.name.title()

            logger.info(f"Creating index file at {index_path}")
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(f"""{"=" * len(dir_name)}
{dir_name}
{"=" * len(dir_name)}

.. toctree::
   :maxdepth: 2
   :caption: Contents:

""")

        # Update existing index file with new entries
        if index_path.exists() and not dry_run:
            try:
                content = index_path.read_text(encoding="utf-8")
                toctree_match = re.search(
                    r"(\.\. toctree::.*?)(\n\n|\Z)", content, re.DOTALL
                )

                if toctree_match:
                    toctree_content = toctree_match.group(1)

                    # Get files in the directory that should be in the toctree
                    rst_files = [
                        f.stem for f in dir_path.glob("*.rst") if f.name != "index.rst"
                    ]

                    # Check for existing entries
                    existing_entries = re.findall(r"   ([^\n]+)", toctree_content)
                    existing_entries = [e.strip() for e in existing_entries]

                    # Add new entries that don't already exist
                    new_entries = []
                    for f in rst_files:
                        if f not in existing_entries and f != "index":
                            new_entries.append(f"   {f}")

                    if new_entries:
                        # Insert new entries at the end of the toctree
                        new_toctree = toctree_content + "\n" + "\n".join(new_entries)
                        new_content = content.replace(toctree_content, new_toctree)

                        logger.info(
                            f"Updating index file {index_path} with new entries: {', '.join(new_entries)}"
                        )
                        index_path.write_text(new_content, encoding="utf-8")
            except Exception as e:
                logger.error(f"Error updating index file {index_path}: {str(e)}")


def fix_documentation_structure(dry_run: bool = False, verbose: bool = False) -> None:
    """
    Main function to fix documentation structure.

    Args:
        dry_run: If True, don't actually move files, just show what would be done
        verbose: If True, show additional logging information
    """
    if verbose:
        logger.setLevel(logging.DEBUG)

    if dry_run:
        logger.info("Running in dry-run mode. No files will be moved.")

    # Ensure all required directories exist
    ensure_directories_exist()

    # Get all documentation files
    all_files = get_all_doc_files()
    logger.info(f"Found {len(all_files)} files in the docs directory")

    # Determine which files need to be moved
    files_to_move = []
    for file_path in all_files:
        if should_move_file(file_path):
            target_path, needs_conversion = get_target_location(file_path)
            if target_path:
                files_to_move.append((file_path, target_path, needs_conversion))

    logger.info(f"Found {len(files_to_move)} files that need to be moved or converted")

    # Process the files
    changes = []
    for file_path, target_path, needs_conversion in files_to_move:
        if needs_conversion:
            logger.info(f"File {file_path} needs to be converted from Markdown to RST")
            if not dry_run:
                rst_file = convert_md_to_rst(file_path)
                if rst_file:
                    # Move the converted file to its target location
                    if move_file(rst_file, target_path, dry_run):
                        changes.append((file_path, target_path))
                    # Delete the original markdown file
                    logger.info(f"Deleting original markdown file: {file_path}")
                    file_path.unlink()
            else:
                # In dry run mode, still record the change
                changes.append((file_path, target_path))
        else:
            # Just move the file
            if move_file(file_path, target_path, dry_run):
                changes.append((file_path, target_path))

    # Update index files
    if changes:
        update_index_files(changes, dry_run)

    # Print summary
    logger.info("=" * 50)
    logger.info("Documentation Structure Fix Summary")
    logger.info("=" * 50)
    logger.info(f"Total files scanned: {len(all_files)}")
    logger.info(f"Files that needed fixes: {len(files_to_move)}")
    logger.info(f"Successful changes: {len(changes)}")

    if changes:
        logger.info("\nChanges made:")
        for source, target in changes:
            logger.info(f"  {source} -> {target}")

    logger.info("=" * 50)


def main():
    """Parse command line arguments and run the script."""
    parser = argparse.ArgumentParser(
        description="Fix documentation structure according to organization rules"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making any changes",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show more detailed logging output"
    )

    args = parser.parse_args()

    try:
        fix_documentation_structure(dry_run=args.dry_run, verbose=args.verbose)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        if args.verbose:
            import traceback

            logger.error(traceback.format_exc())
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
