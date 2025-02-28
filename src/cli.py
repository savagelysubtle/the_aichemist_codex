"""CLI for The Aichemist Codex - File Summarization & Organization."""

import argparse
import logging
from pathlib import Path

from aichemist_codex.file_manager.file_tree import generate_file_tree
from aichemist_codex.project_reader.code_summary import summarize_project

logger = logging.getLogger(__name__)


def validate_directory(directory: Path) -> Path:
    """Ensure the given directory exists and is accessible."""
    resolved_dir = directory.resolve()
    if not resolved_dir.exists() or not resolved_dir.is_dir():
        raise argparse.ArgumentTypeError(f"Directory does not exist: {resolved_dir}")
    return resolved_dir


def main():
    """Entry point for the command-line interface."""
    parser = argparse.ArgumentParser(description="Analyze and summarize project files.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # 🔹 File Tree Generator Command
    tree_parser = subparsers.add_parser("tree", help="Generate a file tree.")
    tree_parser.add_argument(
        "directory", type=validate_directory, help="Directory to analyze."
    )
    tree_parser.add_argument(
        "--output", type=Path, help="Output JSON file for file tree."
    )

    # 🔹 Code Summarization Command
    summary_parser = subparsers.add_parser("summarize", help="Summarize Python code.")
    summary_parser.add_argument(
        "directory", type=validate_directory, help="Directory to analyze."
    )
    summary_parser.add_argument(
        "--output-format",
        choices=["json", "md"],
        default="json",
        help="Output format (default: JSON).",
    )

    args = parser.parse_args()

    # ✅ File Tree Generation
    if args.command == "tree":
        output_file = args.output or args.directory / "file_tree.json"
        logger.info(f"Generating file tree for {args.directory}")
        generate_file_tree(args.directory, output_file)
        logger.info(f"File tree saved to {output_file}")

    # ✅ Code Summarization
    elif args.command == "summarize":
        output_json_file = args.directory / "code_summary.json"
        output_md_file = args.directory / "code_summary.md"

        logger.info(f"Analyzing Python code in {args.directory}")
        summarize_project(args.directory, output_md_file, output_json_file)

        if args.output_format == "json":
            logger.info(f"Code summary saved to {output_json_file}")
        elif args.output_format == "md":
            logger.info(f"Markdown summary saved to {output_md_file}")


if __name__ == "__main__":
    main()
