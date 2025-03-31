"""
AIchemist Codex File Migration Script (JSON-based)
- Loads migration configuration from a JSON file
- Includes retry logic for Windows permission issues
- Updates import statements in migrated files

Usage:
    python desktopscript.py                          # Uses reader_migration_plan.json by default
    python desktopscript.py --config path/to/file.json   # Specify a different JSON file
    python desktopscript.py --project-root "D:/path/to/project"  # Specify project root

JSON file format:
[
  {
    "source": "relative/path/to/source/file.py",
    "destination": "relative/path/to/destination/file.py",
    "imports_to_update": {
      "from old.import": "from new.import",
      "import old.module": "import new.module"
    }
  },
  ...
]

IMPORTANT: Always backup your code before running this script!
This script will delete source files after moving them.
"""

import argparse
import json
import logging
import os
import sys
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("migration_log.txt"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# PROJECT PATH - EDIT THIS TO MATCH YOUR PROJECT LOCATION
PROJECT_ROOT = r"D:\Coding\Python_Projects\the_aichemist_codex"


def ensure_directory_exists(file_path):
    """Create directory structure if it doesn't exist"""
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")


def update_imports(file_content, import_mappings):
    """Update import statements in the file content"""
    updated_content = file_content
    for old_import, new_import in import_mappings.items():
        updated_content = updated_content.replace(old_import, new_import)
    return updated_content


def move_file_with_retry(
    source, destination, import_mappings=None, max_retries=5, delay=2
):
    """Move a file with retry logic for Windows permission issues"""
    source_path = os.path.join(PROJECT_ROOT, source)
    dest_path = os.path.join(PROJECT_ROOT, destination)

    # Check if source exists
    if not os.path.exists(source_path):
        logger.error(f"Source file not found: {source_path}")
        return False

    # Ensure destination directory exists
    ensure_directory_exists(dest_path)

    # Try to move the file with retries
    for attempt in range(max_retries):
        try:
            # Read the file content
            with open(source_path, encoding="utf-8") as f:
                content = f.read()

            # Update imports if needed
            if import_mappings:
                content = update_imports(content, import_mappings)

            # Write to destination
            with open(dest_path, "w", encoding="utf-8") as f:
                f.write(content)

            # If successful, delete the source file
            os.remove(source_path)
            logger.info(f"Successfully moved and updated: {source} -> {destination}")
            return True

        except PermissionError as e:
            logger.warning(
                f"Permission error (attempt {attempt + 1}/{max_retries}): {e}"
            )
            time.sleep(delay)
        except Exception as e:
            logger.error(f"Error moving file: {e}")
            return False

    logger.error(f"Failed to move file after {max_retries} attempts: {source}")
    return False


def load_migration_plan(json_file_path):
    """Load migration operations from a JSON file"""
    try:
        with open(json_file_path, encoding="utf-8") as f:
            migration_plan = json.load(f)
        logger.info(f"Loaded migration plan from {json_file_path}")
        return migration_plan
    except FileNotFoundError:
        logger.error(f"Migration plan file not found: {json_file_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in migration plan: {e}")
        return []
    except Exception as e:
        logger.error(f"Error loading migration plan: {e}")
        return []


def check_existing_files():
    """Map what files actually exist in the backend structure"""
    backend_root = os.path.join(
        PROJECT_ROOT, "src", "the_aichemist_codex", "backend", "core"
    )
    actual_files = []

    for root, _, files in os.walk(backend_root):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, PROJECT_ROOT)
                actual_files.append(rel_path.replace("/", "\\"))

    return actual_files


def main():
    """Main migration function"""
    global PROJECT_ROOT

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="AIchemist Codex File Migration Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python desktopscript.py
  python desktopscript.py --config other_migration_plan.json
  python desktopscript.py --project-root "D:/my_project_root"
        """,
    )
    parser.add_argument(
        "--config",
        "-c",
        default="reader_migration_plan.json",
        help="Path to the JSON migration configuration file (default: reader_migration_plan.json)",
    )
    parser.add_argument(
        "--project-root",
        "-p",
        default=PROJECT_ROOT,
        help="Root directory of the project (default: hardcoded path)",
    )

    # For running as a standalone script without arguments
    if os.path.exists("reader_migration_plan.json") and len(sys.argv) == 1:
        json_path = "reader_migration_plan.json"
    else:
        args = parser.parse_args()
        json_path = args.config
        if args.project_root != PROJECT_ROOT:
            PROJECT_ROOT = args.project_root

    logger.info("Starting AIchemist Codex file migration...")
    logger.info(f"Project root: {PROJECT_ROOT}")
    logger.info(f"Configuration file: {json_path}")

    # Load migration operations from JSON file
    operations = load_migration_plan(json_path)
    if not operations:
        logger.error("No migration operations found. Exiting.")
        return

    logger.info(f"Loaded {len(operations)} migration operations")

    # Find what files actually exist
    existing_files = check_existing_files()
    logger.info(f"Found {len(existing_files)} Python files in backend/core")

    success_count = 0
    failed_files = []

    # Verify all source files in the migration list exist
    for operation in operations:
        source_path = os.path.join(PROJECT_ROOT, operation["source"])
        if not os.path.exists(source_path):
            logger.warning(f"Source file not found: {source_path}")

    # Perform migrations
    for i, operation in enumerate(operations, 1):
        logger.info(f"Processing {i}/{len(operations)}: {operation['source']}")

        if move_file_with_retry(
            operation["source"],
            operation["destination"],
            operation.get("imports_to_update", {}),
        ):
            success_count += 1
        else:
            failed_files.append(operation["source"])

    # Report results
    logger.info(
        f"Migration completed. {success_count}/{len(operations)} files moved successfully."
    )
    if failed_files:
        logger.warning("Failed to move these files:")
        for file in failed_files:
            logger.warning(f"  - {file}")

    print("\nPress Enter to exit...")
    input()


if __name__ == "__main__":
    main()
