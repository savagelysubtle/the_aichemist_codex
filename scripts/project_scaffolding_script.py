#!/usr/bin/env python3
"""Project Scaffolding Script.

This script creates a directory structure for a project based on user input.
It checks for existing directories at each level and skips them while continuing
to create their child directories if they don't exist.
"""

import argparse
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Command line arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Create project directory structure from a template"
    )
    parser.add_argument(
        "--input",
        type=str,
        help="Path to JSON file containing the directory structure",
    )
    parser.add_argument(
        "--root",
        type=str,
        default=".",
        help="Root directory where the project structure will be created (default: current directory)",
    )
    parser.add_argument(
        "--create-files",
        action="store_true",
        help="Create placeholder files defined in the structure",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without actually creating anything",
    )
    return parser.parse_args()


def load_structure(input_file: str | Path) -> dict:
    """Load the directory structure from a JSON file.

    Args:
        input_file: Path to the JSON file containing the directory structure

    Returns:
        Dictionary representing the directory structure

    Raises:
        FileNotFoundError: If the input file doesn't exist
        json.JSONDecodeError: If the input file is not valid JSON
    """
    try:
        with open(input_file) as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Input file not found: {input_file}")
        raise
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in input file: {input_file}")
        raise


def create_directory_structure(
    structure: dict,
    root_path: Path,
    create_files: bool = False,
    dry_run: bool = False,
) -> None:
    """Recursively create a directory structure.

    This function creates directories based on the provided structure.
    If a directory already exists, it skips creating that directory but
    still processes its children.

    Args:
        structure: Dictionary representing the directory structure
        root_path: Base path where the structure will be created
        create_files: Whether to create placeholder files
        dry_run: If True, only show what would be created without making changes
    """
    # Create directories in the structure
    for dir_name, contents in structure.get("directories", {}).items():
        dir_path = root_path / dir_name

        # Check if the directory already exists
        if dir_path.exists():
            logger.info(f"Directory already exists (skipping): {dir_path}")
        else:
            if not dry_run:
                try:
                    dir_path.mkdir(parents=False, exist_ok=True)
                    logger.info(f"Created directory: {dir_path}")
                except OSError as e:
                    logger.error(f"Failed to create directory {dir_path}: {e}")
                    continue
            else:
                logger.info(f"Would create directory: {dir_path}")

        # Process the subdirectories and files in this directory
        if isinstance(contents, dict):
            create_directory_structure(contents, dir_path, create_files, dry_run)

    # Create files if requested
    if create_files:
        for file_name, file_content in structure.get("files", {}).items():
            file_path = root_path / file_name

            if file_path.exists():
                logger.info(f"File already exists (skipping): {file_path}")
            else:
                if not dry_run:
                    try:
                        with open(file_path, "w") as f:
                            f.write(file_content or "")
                        logger.info(f"Created file: {file_path}")
                    except OSError as e:
                        logger.error(f"Failed to create file {file_path}: {e}")
                else:
                    logger.info(f"Would create file: {file_path}")


def create_sample_structure() -> dict:
    """Create a sample directory structure for demonstration.

    Returns:
        Dictionary containing a sample project structure
    """
    return {
        "directories": {
            "src": {
                "directories": {
                    "the_aichemist_codex": {
                        "directories": {
                            "backend": {
                                "directories": {
                                    "api": {},
                                    "core": {
                                        "directories": {
                                            "files": {},
                                            "content": {},
                                            "tagging": {},
                                            "search": {},
                                            "versioning": {},
                                        }
                                    },
                                    "common": {},
                                    "infrastructure": {
                                        "directories": {
                                            "utils": {},
                                            "config": {},
                                            "notification": {},
                                        }
                                    },
                                    "cli": {},
                                },
                                "files": {
                                    "__init__.py": "",
                                    "main.py": "# Main entry point for the backend\n",
                                },
                            },
                            "middleware": {
                                "directories": {
                                    "adapters": {},
                                    "services": {},
                                },
                                "files": {
                                    "__init__.py": "",
                                },
                            },
                            "frontend": {
                                "directories": {
                                    "ui": {},
                                    "views": {},
                                    "controllers": {},
                                },
                                "files": {
                                    "__init__.py": "",
                                },
                            },
                        },
                        "files": {
                            "__init__.py": "",
                        },
                    }
                }
            },
            "tests": {
                "directories": {
                    "unit": {},
                    "integration": {},
                    "e2e": {},
                },
            },
            "docs": {
                "directories": {
                    "api": {},
                    "guides": {},
                },
            },
            "scripts": {},
            "data": {
                "directories": {
                    "raw": {},
                    "processed": {},
                },
            },
        },
        "files": {
            "README.md": "# The Aichemist Codex\n\nProject for managing and organizing content.\n",
            "pyproject.toml": '[build-system]\nrequires = ["setuptools>=42", "wheel"]\nbuild-backend = "setuptools.build_meta"\n',
            ".gitignore": "__pycache__/\n*.py[cod]\n*$py.class\n*.so\n.Python\n",
        },
    }


def interactive_structure_builder() -> dict:
    """Build a directory structure interactively.

    Returns:
        Dictionary representing the directory structure
    """
    structure = {"directories": {}, "files": {}}

    print("Interactive Project Structure Builder")
    print("------------------------------------")
    print("Enter directory and file paths to create.")
    print("For directories, end with a '/'")
    print("For files, you can optionally specify content after a ':' character")
    print("Enter an empty line to finish.")
    print("")

    while True:
        path = input("Enter path (or empty line to finish): ").strip()
        if not path:
            break

        # Handle files with content
        content = None
        if ":" in path and not path.endswith("/"):
            path, content = path.split(":", 1)

        # Create the path in the structure
        if path.endswith("/"):
            # It's a directory
            path = path.rstrip("/")
            current = structure["directories"]
            parts = path.split("/")

            for i, part in enumerate(parts):
                if part not in current:
                    current[part] = {"directories": {}, "files": {}}

                if i < len(parts) - 1:
                    current = current[part]["directories"]

        else:
            # It's a file
            parts = path.split("/")
            filename = parts[-1]

            # Navigate to the correct directory
            current = structure
            for part in parts[:-1]:
                if part not in current["directories"]:
                    current["directories"][part] = {"directories": {}, "files": {}}
                current = current["directories"][part]

            # Add the file
            current["files"][filename] = content or ""

    return structure


def main() -> None:
    """Main function to run the script."""
    args = parse_arguments()

    # Set up logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Convert root path to Path object
    root_path = Path(args.root).absolute()
    logger.info(f"Root directory: {root_path}")

    # Load or create the structure
    if args.input:
        logger.info(f"Loading structure from {args.input}")
        structure = load_structure(args.input)
    else:
        logger.info("No input file provided. Using interactive mode.")
        structure = interactive_structure_builder()

        # Ask if user wants to save this structure for future use
        save = input(
            "Do you want to save this structure for future use? (y/n): "
        ).lower()
        if save == "y":
            output_file = input("Enter filename to save structure: ")
            with open(output_file, "w") as f:
                json.dump(structure, f, indent=2)
            logger.info(f"Structure saved to {output_file}")

    # Create the directory structure
    logger.info("Creating directory structure...")
    if args.dry_run:
        logger.info("DRY RUN: No files or directories will be created")

    create_directory_structure(structure, root_path, args.create_files, args.dry_run)

    logger.info("Done!")


if __name__ == "__main__":
    main()
