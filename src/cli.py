# Comprehensive CLI for The Aichemist Codex

import argparse
import logging
from pathlib import Path

from aichemist_codex.file_manager.duplicate_detector import (
    DuplicateDetector as find_duplicates,
)
from aichemist_codex.file_manager.file_tree import (
    FileTreeGenerator as generate_file_tree,
)
from aichemist_codex.file_manager.file_watcher import FileEventHandler as start_watcher
from aichemist_codex.file_manager.sorter import RuleBasedSorter as sort_files
from aichemist_codex.file_reader.file_reader import FileReader
from aichemist_codex.ingest.aggregator import aggregate_digest as aggregate_content
from aichemist_codex.ingest.scanner import scan_directory
from aichemist_codex.output_formatter.json_writer import (
    save_as_json_async as write_json,
)
from aichemist_codex.output_formatter.markdown_writer import (
    save_as_markdown as write_markdown,
)
from aichemist_codex.project_reader.code_summary import summarize_project
from aichemist_codex.project_reader.notebooks import (
    NotebookConverter as convert_notebooks,
)
from aichemist_codex.project_reader.token_counter import TokenAnalyzer as count_tokens
from aichemist_codex.search.search_engine import SearchEngine

logger = logging.getLogger(__name__)


def validate_directory(directory) -> Path:
    """Ensure the given directory exists and is accessible."""
    directory = Path(directory)
    resolved_dir = directory.resolve()
    if not resolved_dir.exists() or not resolved_dir.is_dir():
        raise argparse.ArgumentTypeError(f"Directory does not exist: {resolved_dir}")
    return resolved_dir


def main():
    """Entry point for the command-line interface."""
    parser = argparse.ArgumentParser(
        description="The Aichemist Codex: File Analysis & Organization Tool"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # 🔹 File Tree Generator Command
    tree_parser = subparsers.add_parser("tree", help="Generate a file tree.")
    tree_parser.add_argument(
        "directory", type=validate_directory, help="Directory to analyze."
    )
    tree_parser.add_argument(
        "--output", type=Path, help="Output JSON file for file tree."
    )
    tree_parser.add_argument(
        "--depth", type=int, default=None, help="Maximum depth of the file tree."
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
    summary_parser.add_argument(
        "--include-notebooks",
        action="store_true",
        help="Include Jupyter notebooks in the summary.",
    )

    # 🔹 File Sorting Command
    sort_parser = subparsers.add_parser("sort", help="Sort files according to rules.")
    sort_parser.add_argument(
        "directory", type=validate_directory, help="Directory containing files to sort."
    )
    sort_parser.add_argument(
        "--config", type=Path, help="Configuration file with sorting rules."
    )
    sort_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes.",
    )

    # 🔹 Duplicate Detection Command
    dupes_parser = subparsers.add_parser("duplicates", help="Find duplicate files.")
    dupes_parser.add_argument(
        "directory", type=validate_directory, help="Directory to scan for duplicates."
    )
    dupes_parser.add_argument(
        "--output", type=Path, help="Output file to save results (JSON)."
    )
    dupes_parser.add_argument(
        "--method",
        choices=["hash", "name", "content"],
        default="hash",
        help="Method to use for detecting duplicates.",
    )

    # 🔹 File Watcher Command
    watch_parser = subparsers.add_parser("watch", help="Watch directory for changes.")
    watch_parser.add_argument(
        "directory", type=validate_directory, help="Directory to watch."
    )
    watch_parser.add_argument(
        "--config", type=Path, help="Configuration file for watch actions."
    )
    watch_parser.add_argument(
        "--recursive", action="store_true", help="Watch subdirectories recursively."
    )

    # 🔹 Notebook Conversion Command
    notebook_parser = subparsers.add_parser(
        "notebooks", help="Convert Jupyter notebooks to other formats."
    )
    notebook_parser.add_argument(
        "directory", type=validate_directory, help="Directory containing notebooks."
    )
    notebook_parser.add_argument(
        "--output-format",
        choices=["py", "md", "html"],
        default="py",
        help="Output format for notebooks.",
    )
    notebook_parser.add_argument(
        "--recursive", action="store_true", help="Process subdirectories recursively."
    )

    # 🔹 Token Counting Command
    token_parser = subparsers.add_parser("tokens", help="Count tokens in text files.")
    token_parser.add_argument(
        "directory", type=validate_directory, help="Directory containing files."
    )
    token_parser.add_argument(
        "--output", type=Path, help="Output file for token counts (JSON)."
    )
    token_parser.add_argument(
        "--model",
        type=str,
        default="gpt-3.5-turbo",
        help="Model for token calculation.",
    )

    # 🔹 Search Command
    search_parser = subparsers.add_parser("search", help="Search through files.")
    search_parser.add_argument(
        "directory", type=validate_directory, help="Directory to search."
    )
    search_parser.add_argument("query", type=str, help="Search query.")
    search_parser.add_argument(
        "--method",
        choices=["filename", "fulltext", "fuzzy"],
        default="fulltext",
        help="Search method to use.",
    )
    search_parser.add_argument(
        "--output", type=Path, help="Output file for search results."
    )

    # 🔹 Ingest Command
    ingest_parser = subparsers.add_parser("ingest", help="Scan and ingest files.")
    ingest_parser.add_argument(
        "directory", type=validate_directory, help="Directory to ingest."
    )
    ingest_parser.add_argument(
        "--output", type=Path, help="Output file for ingestion results."
    )
    ingest_parser.add_argument(
        "--include", nargs="+", help="Patterns for files to include."
    )
    ingest_parser.add_argument(
        "--ignore", nargs="+", help="Patterns for files to ignore."
    )

    # 🔹 Read File Command
    read_parser = subparsers.add_parser("read", help="Read and display file content.")
    read_parser.add_argument("file", type=Path, help="File to read.")
    read_parser.add_argument(
        "--format",
        choices=["auto", "text", "json", "html", "markdown"],
        default="auto",
        help="Output format.",
    )
    read_parser.add_argument(
        "--extract-text",
        action="store_true",
        help="Extract text from non-text files (PDF, images etc).",
    )

    args = parser.parse_args()

    # ✅ File Tree Generation
    if args.command == "tree":
        logger.info(f"Generating file tree for {args.directory}")
        # Instantiate the FileTreeGenerator and call its generate() method.
        tree_generator = generate_file_tree()
        file_tree = tree_generator.generate(args.directory, max_depth=args.depth)
        output_file = args.output or args.directory / "file_tree.json"
        write_json(file_tree, output_file)
        logger.info(f"File tree saved to {output_file}")

    # ✅ Code Summarization
    elif args.command == "summarize":
        output_json_file = args.directory / "code_summary.json"
        output_md_file = args.directory / "code_summary.md"

        logger.info(f"Analyzing code in {args.directory}")
        summarize_project(
            args.directory,
            output_md_file,
            output_json_file,
            include_notebooks=args.include_notebooks,
        )

        if args.output_format == "json":
            logger.info(f"Code summary saved to {output_json_file}")
        elif args.output_format == "md":
            logger.info(f"Markdown summary saved to {output_md_file}")

    # ✅ File Sorting
    elif args.command == "sort":
        logger.info(f"Sorting files in {args.directory}")
        sort_files(args.directory, config_file=args.config, dry_run=args.dry_run)
        logger.info("File sorting completed")

    # ✅ Duplicate Detection
    elif args.command == "duplicates":
        output_file = args.output or args.directory / "duplicates.json"
        logger.info(f"Scanning for duplicates in {args.directory}")
        duplicates = find_duplicates(args.directory, method=args.method)
        write_json(duplicates, output_file)
        logger.info(f"Found {len(duplicates)} duplicate sets, saved to {output_file}")

    # ✅ File Watcher
    elif args.command == "watch":
        logger.info(f"Starting file watcher for {args.directory}")
        start_watcher(args.directory, config_file=args.config, recursive=args.recursive)
        # This will run until terminated

    # ✅ Notebook Conversion
    elif args.command == "notebooks":
        logger.info(f"Converting notebooks in {args.directory}")
        convert_notebooks(
            args.directory, output_format=args.output_format, recursive=args.recursive
        )
        logger.info("Notebook conversion completed")

    # ✅ Token Counting
    elif args.command == "tokens":
        output_file = args.output or args.directory / "token_counts.json"
        logger.info(f"Counting tokens in {args.directory}")
        token_counts = count_tokens(args.directory, model=args.model)
        write_json(token_counts, output_file)
        logger.info(f"Token counts saved to {output_file}")

    # ✅ Search
    elif args.command == "search":
        output_file = args.output
        logger.info(f"Searching for '{args.query}' in {args.directory}")
        search_engine = SearchEngine(args.directory)
        results = search_engine.search(args.query, method=args.method)

        if output_file:
            write_json(results, output_file)
            logger.info(f"Search results saved to {output_file}")
        else:
            # Print results to console
            for result in results:
                print(f"{result['path']} - Score: {result['score']}")
                if result.get("snippet"):
                    print(f"  {result['snippet']}")
                print()

    # ✅ Ingest
    elif args.command == "ingest":
        include_patterns = set(args.include) if args.include else {"*"}
        ignore_patterns = set(args.ignore) if args.ignore else set()

        logger.info(f"Scanning directory: {args.directory}")
        files = scan_directory(args.directory, include_patterns, ignore_patterns)

        logger.info(f"Ingesting {len(files)} files")
        content = aggregate_content(files)

        if args.output:
            write_json(content, args.output)
            logger.info(f"Ingestion results saved to {args.output}")
        else:
            logger.info(f"Ingested {len(content)} files successfully")

    # ✅ Read File
    elif args.command == "read":
        if not args.file.exists():
            logger.error(f"File does not exist: {args.file}")
            return

        logger.info(f"Reading file: {args.file}")
        # Call FileReader as a callable with the file and extract_text flag.
        content = FileReader(args.file, extract_text=args.extract_text)

        # Output content based on format
        if args.format == "auto":
            print(content)
        elif args.format == "json":
            if args.output:
                write_json(content, args.output)
                logger.info(f"JSON output saved to {args.output}")
            else:
                print(content)
        elif args.format == "markdown":
            if args.output:
                write_markdown(content, args.output)
                logger.info(f"Markdown output saved to {args.output}")
            else:
                md_content = write_markdown(content, None)
                print(md_content)
        else:
            print(content)


if __name__ == "__main__":
    main()
