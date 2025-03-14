"""Command-line interface for The Aichemist Codex."""

import argparse
import asyncio
import logging
from pathlib import Path

from backend.file_manager.duplicate_detector import DuplicateDetector
from backend.file_manager.file_tree import FileTreeGenerator
from backend.file_manager.file_watcher import FileEventHandler
from backend.file_manager.sorter import RuleBasedSorter
from backend.file_reader.file_reader import FileReader
from backend.ingest.aggregator import aggregate_digest
from backend.ingest.scanner import scan_directory
from backend.output_formatter.json_writer import save_as_json_async
from backend.output_formatter.markdown_writer import save_as_markdown
from backend.project_reader.code_summary import summarize_project
from backend.project_reader.notebooks import NotebookConverter
from backend.project_reader.token_counter import TokenAnalyzer
from backend.rollback.rollback_manager import RollbackManager
from backend.search.search_engine import SearchEngine
from backend.utils.cache_manager import CacheManager

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

    # Existing commands (tree, summarize, sort, duplicates, watch, notebooks, tokens, search, ingest, read) ...
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

    search_parser = subparsers.add_parser("search", help="Search through files.")
    search_parser.add_argument(
        "directory", type=validate_directory, help="Directory to search."
    )
    search_parser.add_argument("query", type=str, help="Search query.")
    search_parser.add_argument(
        "--method",
        choices=["filename", "fulltext", "fuzzy", "regex"],
        default="fulltext",
        help="Search method to use.",
    )
    search_parser.add_argument(
        "--output", type=Path, help="Output file for search results."
    )
    search_parser.add_argument(
        "--case-sensitive",
        action="store_true",
        help="Enable case-sensitive search (for regex and fulltext).",
    )
    search_parser.add_argument(
        "--whole-word",
        action="store_true",
        help="Match whole words only (for regex search).",
    )

    # Add similarity search commands
    similarity_parser = subparsers.add_parser(
        "similarity", help="Find similar files using vector embeddings."
    )
    similarity_subparsers = similarity_parser.add_subparsers(
        dest="similarity_command", required=True
    )

    # Command to find files similar to a given file
    similar_parser = similarity_subparsers.add_parser(
        "find", help="Find files similar to a given file."
    )
    similar_parser.add_argument(
        "file", type=Path, help="File to find similar files for."
    )
    similar_parser.add_argument(
        "directory", type=validate_directory, help="Directory to search in."
    )
    similar_parser.add_argument(
        "--threshold", type=float, help="Minimum similarity score (0.0-1.0)."
    )
    similar_parser.add_argument(
        "--max-results",
        type=int,
        default=20,
        help="Maximum number of results to return.",
    )
    similar_parser.add_argument(
        "--output", type=Path, help="Output file for similarity results."
    )

    # Command to find groups of similar files
    groups_parser = similarity_subparsers.add_parser(
        "groups", help="Find groups of similar files."
    )
    groups_parser.add_argument(
        "directory", type=validate_directory, help="Directory to analyze."
    )
    groups_parser.add_argument(
        "--threshold", type=float, help="Similarity threshold for group membership."
    )
    groups_parser.add_argument(
        "--min-group-size",
        type=int,
        default=2,
        help="Minimum number of files to form a group.",
    )
    groups_parser.add_argument(
        "--output", type=Path, help="Output file for group results."
    )

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
    # New: Rollback Management CLI Commands
    rollback_parser = subparsers.add_parser(
        "rollback", help="Manage rollback operations."
    )
    rollback_subparsers = rollback_parser.add_subparsers(
        dest="rollback_command", required=True
    )
    rollback_subparsers.add_parser("last", help="Undo the last operation.")
    rollback_subparsers.add_parser("list", help="List recorded rollback operations.")
    rollback_subparsers.add_parser("redo", help="Redo the last undone operation.")
    rollback_subparsers.add_parser("clear", help="Clear all rollback history.")

    args = parser.parse_args()
    rm = RollbackManager()

    # ✅ File Tree Generation
    if args.command == "tree":
        logger.info(f"Generating file tree for {args.directory}")
        tree_generator = FileTreeGenerator()
        file_tree = asyncio.run(tree_generator.generate(args.directory))
        output_file = args.output or args.directory / "file_tree.json"
        asyncio.run(save_as_json_async(file_tree, output_file))
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

    elif args.command == "sort":
        logger.info(f"Sorting files in {args.directory}")
        sorter = RuleBasedSorter()
        sorter.sort_directory_sync(args.directory)
        logger.info("File sorting completed")

    elif args.command == "duplicates":
        output_file = args.output or args.directory / "duplicates.json"
        logger.info(f"Scanning for duplicates in {args.directory}")
        duplicate_detector = DuplicateDetector()
        duplicate_detector = asyncio.run(
            duplicate_detector.scan_directory(args.directory, args.method)
        )
        duplicates_dict = duplicate_detector.get_duplicates()
        asyncio.run(save_as_json_async(duplicates_dict, output_file))
        logger.info(
            f"Found {len(duplicates_dict)} duplicate sets, saved to {output_file}"
        )

    elif args.command == "watch":
        logger.info(f"Starting file watcher for {args.directory}")
        event_handler = FileEventHandler(args.directory)
        try:
            from watchdog.observers import Observer

            observer = Observer()
            observer.schedule(
                event_handler, str(args.directory), recursive=args.recursive
            )
            observer.start()
            try:
                while True:
                    import time

                    time.sleep(1)
            except KeyboardInterrupt:
                observer.stop()
            observer.join()
        except KeyboardInterrupt:
            logger.info("File watcher stopped")

    elif args.command == "notebooks":
        logger.info(f"Converting notebooks in {args.directory}")
        notebook_converter = NotebookConverter()
        if args.recursive:
            for notebook_file in args.directory.rglob("*.ipynb"):
                if args.output_format == "py":
                    output = notebook_converter.to_script(notebook_file)
                    with open(notebook_file.with_suffix(".py"), "w") as f:
                        f.write(output)
        else:
            for notebook_file in args.directory.glob("*.ipynb"):
                if args.output_format == "py":
                    output = notebook_converter.to_script(notebook_file)
                    with open(notebook_file.with_suffix(".py"), "w") as f:
                        f.write(output)
        logger.info("Notebook conversion completed")

    elif args.command == "tokens":
        output_file = args.output or args.directory / "token_counts.json"
        logger.info(f"Counting tokens in {args.directory}")
        token_analyzer = TokenAnalyzer()
        token_counts = token_analyzer.analyze_directory(
            args.directory, model=args.model
        )
        asyncio.run(save_as_json_async(token_counts, output_file))
        logger.info(f"Token counts saved to {output_file}")

    elif args.command == "search":
        output_file = args.output
        logger.info(f"Searching for '{args.query}' in {args.directory}")

        # Initialize search engine with cache manager for better performance
        cache_manager = CacheManager()
        search_engine = SearchEngine(args.directory, cache_manager=cache_manager)

        # Handle different search methods
        if args.method == "regex":
            logger.info(f"Performing regex search with pattern: {args.query}")
            results = asyncio.run(
                search_engine.regex_search_async(
                    args.query,
                    case_sensitive=args.case_sensitive,
                    whole_word=args.whole_word,
                )
            )
            # Format results for display
            formatted_results = [{"path": path, "score": 1.0} for path in results]
        else:
            # Use existing search methods
            results = search_engine.search(
                args.query,
                method=args.method,
                case_sensitive=(
                    args.case_sensitive if args.method == "fulltext" else False
                ),
            )
            formatted_results = results

        if output_file:
            asyncio.run(save_as_json_async(formatted_results, output_file))
            logger.info(f"Search results saved to {output_file}")
        else:
            for result in formatted_results:
                print(f"{result['path']} - Score: {result.get('score', 1.0)}")
                if result.get("snippet"):
                    print(f"  {result['snippet']}")
                print()

    elif args.command == "similarity":
        # Initialize search engine with cache manager for better performance
        cache_manager = CacheManager()
        search_engine = SearchEngine(args.directory, cache_manager=cache_manager)

        # Handle similarity search commands
        if args.similarity_command == "find":
            file_path = args.file
            output_file = args.output

            if not file_path.exists():
                logger.error(f"File does not exist: {file_path}")
                return

            logger.info(f"Finding files similar to: {file_path}")

            # Find similar files
            similar_files = asyncio.run(
                search_engine.find_similar_files_async(
                    file_path=file_path,
                    threshold=args.threshold,
                    max_results=args.max_results,
                )
            )

            if output_file:
                asyncio.run(save_as_json_async(similar_files, output_file))
                logger.info(f"Similarity results saved to {output_file}")
            else:
                if not similar_files:
                    print(f"No similar files found for {file_path}")
                else:
                    print(f"Found {len(similar_files)} files similar to {file_path}:")
                    for result in similar_files:
                        similarity = result["similarity"] * 100  # Convert to percentage
                        print(f"{result['path']} - Similarity: {similarity:.2f}%")
                    print()

        elif args.similarity_command == "groups":
            output_file = args.output
            logger.info(f"Finding groups of similar files in: {args.directory}")

            # Find file groups
            file_groups = asyncio.run(
                search_engine.find_file_groups_async(
                    threshold=args.threshold, min_group_size=args.min_group_size
                )
            )

            if output_file:
                asyncio.run(save_as_json_async(file_groups, output_file))
                logger.info(f"File groups saved to {output_file}")
            else:
                if not file_groups:
                    print("No groups of similar files found")
                else:
                    print(f"Found {len(file_groups)} groups of similar files:")
                    for i, group in enumerate(file_groups, 1):
                        print(f"\nGroup {i} ({len(group)} files):")
                        for file_path in group:
                            print(f"  {file_path}")
                    print()

    elif args.command == "ingest":
        include_patterns = set(args.include) if args.include else {"*"}
        ignore_patterns = set(args.ignore) if args.ignore else set()
        logger.info(f"Scanning directory: {args.directory}")
        files = scan_directory(args.directory, include_patterns, ignore_patterns)
        logger.info(f"Ingesting {len(files)} files")
        content = aggregate_digest(files)
        if args.output:
            asyncio.run(save_as_json_async(content, args.output))
            logger.info(f"Ingestion results saved to {args.output}")
        else:
            logger.info(f"Ingested {len(content)} files successfully")

    elif args.command == "read":
        if not args.file.exists():
            logger.error(f"File does not exist: {args.file}")
            return
        logger.info(f"Reading file: {args.file}")
        reader = FileReader()
        reader.get_mime_types = reader.get_mime_types(args.file)
        metadata = asyncio.run(reader.process_file(args.file))
        content = metadata.preview
        if args.format == "auto":
            print(content)
        elif args.format == "json":
            if args.output:
                asyncio.run(save_as_json_async(metadata.to_dict(), args.output))
                logger.info(f"JSON output saved to {args.output}")
            else:
                print(content)
        elif args.format == "markdown":
            if args.output:
                save_as_markdown(content, args.output)
                logger.info(f"Markdown output saved to {args.output}")
            else:
                md_content = save_as_markdown(content, None)
                print(md_content)
        else:
            print(content)

    elif args.command == "rollback":
        if args.rollback_command == "last":
            success = asyncio.run(rm.undo_last_operation())
            if success:
                logger.info("Successfully rolled back the last operation.")
            else:
                logger.error("Failed to roll back the last operation.")
        elif args.rollback_command == "list":
            ops = [op.to_dict() for op in rm._undo_stack]
            if ops:
                for op in ops:
                    print(op)
            else:
                print("No rollback operations recorded.")
        elif args.rollback_command == "redo":
            success = asyncio.run(rm.redo_last_undone())
            if success:
                logger.info("Successfully redid the last undone operation.")
            else:
                logger.error("Failed to redo the last operation.")
        elif args.rollback_command == "clear":
            rm._undo_stack.clear()
            rm._redo_stack.clear()
            rm.rollback_log.write_text("[]", encoding="utf-8")
            logger.info("Cleared all rollback operations.")


if __name__ == "__main__":
    main()
