"""Command-line interface for The Aichemist Codex."""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

from backend.file_manager.duplicate_detector import DuplicateDetector
from backend.file_manager.file_tree import FileTreeGenerator
from backend.file_manager.file_watcher import FileEventHandler
from backend.file_manager.sorter import RuleBasedSorter
from backend.file_reader.file_reader import FileReader
from backend.ingest.aggregator import aggregate_digest
from backend.ingest.scanner import scan_directory
from backend.metadata.manager import MetadataManager
from backend.output_formatter.json_writer import save_as_json_async
from backend.output_formatter.markdown_writer import save_as_markdown
from backend.project_reader.code_summary import summarize_project
from backend.project_reader.notebooks import NotebookConverter
from backend.project_reader.token_counter import TokenAnalyzer
from backend.relationships.detector import DetectionStrategy, RelationshipDetector
from backend.relationships.detectors.directory_structure import (
    DirectoryStructureDetector,
)
from backend.relationships.graph import RelationshipGraph
from backend.relationships.relationship import RelationshipType
from backend.relationships.store import RelationshipStore
from backend.rollback.rollback_manager import RollbackManager
from backend.search.search_engine import SearchEngine
from backend.tagging.classifier import TagClassifier
from backend.tagging.hierarchy import TagHierarchy
from backend.tagging.manager import TagManager
from backend.tagging.suggester import TagSuggester
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

    # Add metadata extraction command
    metadata_parser = subparsers.add_parser(
        "metadata", help="Extract and analyze metadata from files."
    )
    metadata_subparsers = metadata_parser.add_subparsers(
        dest="metadata_command", required=True
    )

    # Extract metadata from a single file
    extract_parser = metadata_subparsers.add_parser(
        "extract", help="Extract metadata from a single file."
    )
    extract_parser.add_argument(
        "file", type=Path, help="File to extract metadata from."
    )
    extract_parser.add_argument(
        "--output", type=Path, help="Output file to save metadata (JSON)."
    )

    # Extract metadata from all files in a directory
    batch_parser = metadata_subparsers.add_parser(
        "batch", help="Extract metadata from all files in a directory."
    )
    batch_parser.add_argument(
        "directory", type=validate_directory, help="Directory to analyze."
    )
    batch_parser.add_argument(
        "--output", type=Path, help="Output file to save results (JSON)."
    )
    batch_parser.add_argument(
        "--recursive", action="store_true", help="Recursively process subdirectories."
    )
    batch_parser.add_argument(
        "--max-concurrent",
        type=int,
        default=5,
        help="Maximum number of concurrent extraction tasks.",
    )
    batch_parser.add_argument(
        "--pattern", type=str, help="Glob pattern to filter files (e.g., '*.py')."
    )

    # Analyze files and group by metadata properties
    analyze_parser = metadata_subparsers.add_parser(
        "analyze", help="Analyze files and group by metadata properties."
    )
    analyze_parser.add_argument(
        "directory", type=validate_directory, help="Directory to analyze."
    )
    analyze_parser.add_argument(
        "--output", type=Path, help="Output file to save results (JSON)."
    )
    analyze_parser.add_argument(
        "--group-by",
        type=str,
        choices=["tags", "language", "type", "authors"],
        default="tags",
        help="Metadata property to group by.",
    )

    # Add tagging commands
    tags_parser = subparsers.add_parser("tags", help="File tagging operations")
    tags_subparsers = tags_parser.add_subparsers(dest="tags_command", required=True)

    # Tag management commands
    tag_add_parser = tags_subparsers.add_parser("add", help="Add tags to files")
    tag_add_parser.add_argument("file", type=Path, help="File to tag")
    tag_add_parser.add_argument("tags", nargs="+", help="Tags to add")
    tag_add_parser.add_argument(
        "--description", help="Tag description (when creating a new tag)"
    )

    tag_remove_parser = tags_subparsers.add_parser(
        "remove", help="Remove tags from files"
    )
    tag_remove_parser.add_argument("file", type=Path, help="File to modify")
    tag_remove_parser.add_argument("tags", nargs="+", help="Tags to remove")

    tag_list_parser = tags_subparsers.add_parser(
        "list", help="List tags for a file or all tags"
    )
    tag_list_parser.add_argument("--file", type=Path, help="File to show tags for")
    tag_list_parser.add_argument("--output", type=Path, help="Output file for results")

    # Tag suggestion commands
    tag_suggest_parser = tags_subparsers.add_parser(
        "suggest", help="Suggest tags for files"
    )
    tag_suggest_parser.add_argument("file", type=Path, help="File to suggest tags for")
    tag_suggest_parser.add_argument(
        "--threshold", type=float, default=0.6, help="Confidence threshold (0.0-1.0)"
    )
    tag_suggest_parser.add_argument(
        "--apply", action="store_true", help="Apply suggested tags automatically"
    )
    tag_suggest_parser.add_argument(
        "--output", type=Path, help="Output file for suggestions"
    )

    # Batch tagging commands
    tag_batch_parser = tags_subparsers.add_parser(
        "batch", help="Batch tag multiple files"
    )
    tag_batch_parser.add_argument(
        "directory", type=validate_directory, help="Directory to process"
    )
    tag_batch_parser.add_argument(
        "--recursive", action="store_true", help="Process subdirectories recursively"
    )
    tag_batch_parser.add_argument(
        "--pattern", help="File pattern to match (e.g., '*.py')"
    )
    tag_batch_parser.add_argument(
        "--threshold", type=float, default=0.7, help="Confidence threshold (0.0-1.0)"
    )
    tag_batch_parser.add_argument(
        "--apply", action="store_true", help="Apply suggested tags automatically"
    )
    tag_batch_parser.add_argument("--output", type=Path, help="Output file for results")

    # Tag query commands
    tag_find_parser = tags_subparsers.add_parser(
        "find", help="Find files with specific tags"
    )
    tag_find_parser.add_argument("tags", nargs="+", help="Tags to search for")
    tag_find_parser.add_argument(
        "--all", action="store_true", help="Require all tags (AND), default is any (OR)"
    )
    tag_find_parser.add_argument(
        "--threshold", type=float, default=0.0, help="Minimum confidence threshold"
    )
    tag_find_parser.add_argument("--output", type=Path, help="Output file for results")

    # Tag hierarchy management
    tag_hierarchy_parser = tags_subparsers.add_parser(
        "hierarchy", help="Manage tag hierarchies"
    )
    tag_hierarchy_subparsers = tag_hierarchy_parser.add_subparsers(
        dest="hierarchy_command", required=True
    )

    hier_add_parser = tag_hierarchy_subparsers.add_parser(
        "add", help="Add a parent-child relationship"
    )
    hier_add_parser.add_argument("parent", help="Parent tag name")
    hier_add_parser.add_argument("child", help="Child tag name")

    hier_remove_parser = tag_hierarchy_subparsers.add_parser(
        "remove", help="Remove a parent-child relationship"
    )
    hier_remove_parser.add_argument("parent", help="Parent tag name")
    hier_remove_parser.add_argument("child", help="Child tag name")

    hier_show_parser = tag_hierarchy_subparsers.add_parser(
        "show", help="Show tag hierarchy"
    )
    hier_show_parser.add_argument(
        "--tag", help="Root tag to show hierarchy for (optional)"
    )
    hier_show_parser.add_argument(
        "--output", type=Path, help="Output file for hierarchy"
    )

    hier_export_parser = tag_hierarchy_subparsers.add_parser(
        "export", help="Export tag hierarchy"
    )
    hier_export_parser.add_argument(
        "output", type=Path, help="Output file for hierarchy (JSON)"
    )

    hier_import_parser = tag_hierarchy_subparsers.add_parser(
        "import", help="Import tag hierarchy"
    )
    hier_import_parser.add_argument(
        "input", type=Path, help="Input file with hierarchy (JSON)"
    )

    # Classifier management
    tag_classifier_parser = tags_subparsers.add_parser(
        "classifier", help="Manage tag classifier"
    )
    tag_classifier_subparsers = tag_classifier_parser.add_subparsers(
        dest="classifier_command", required=True
    )

    classifier_train_parser = tag_classifier_subparsers.add_parser(
        "train", help="Train the tag classifier"
    )
    classifier_train_parser.add_argument(
        "directory", type=validate_directory, help="Directory with tagged files"
    )
    classifier_train_parser.add_argument(
        "--test-size", type=float, default=0.2, help="Portion of data for testing"
    )

    classifier_info_parser = tag_classifier_subparsers.add_parser(
        "info", help="Show classifier information"
    )
    classifier_info_parser.add_argument(
        "--output", type=Path, help="Output file for information"
    )

    # ---------- File Relationship Mapping Commands ----------
    rel_parser = subparsers.add_parser(
        "relationships", help="File relationship operations"
    )
    rel_subparsers = rel_parser.add_subparsers(dest="rel_command", required=True)

    # Detect relationships command
    detect_parser = rel_subparsers.add_parser(
        "detect", help="Detect relationships between files"
    )
    detect_parser.add_argument(
        "paths", nargs="+", help="Paths to analyze for relationships"
    )
    detect_parser.add_argument(
        "--strategies",
        nargs="+",
        choices=[s.name for s in DetectionStrategy if s != DetectionStrategy.ALL],
        default=["IMPORT_ANALYSIS", "DIRECTORY_STRUCTURE"],
        help="Detection strategies to use",
    )
    detect_parser.add_argument(
        "--db-path",
        type=str,
        default=str(Path.home() / ".aichemist" / "relationships.db"),
        help="Path to the relationships database",
    )

    # Find related files command
    related_parser = rel_subparsers.add_parser(
        "find-related", help="Find files related to a specific file"
    )
    related_parser.add_argument(
        "file_path", help="Path to the file to find related files for"
    )
    related_parser.add_argument(
        "--types",
        nargs="+",
        choices=[t.name for t in RelationshipType],
        help="Relationship types to include",
    )
    related_parser.add_argument(
        "--min-strength",
        type=float,
        default=0.0,
        help="Minimum relationship strength (0.0 to 1.0)",
    )
    related_parser.add_argument(
        "--db-path",
        type=str,
        default=str(Path.home() / ".aichemist" / "relationships.db"),
        help="Path to the relationships database",
    )
    related_parser.add_argument(
        "--output", type=Path, help="Output file for results (JSON)"
    )

    # Find paths between files command
    paths_parser = rel_subparsers.add_parser(
        "find-paths", help="Find paths between two files"
    )
    paths_parser.add_argument("source_path", help="Path to the source file")
    paths_parser.add_argument("target_path", help="Path to the target file")
    paths_parser.add_argument(
        "--max-length", type=int, default=5, help="Maximum path length"
    )
    paths_parser.add_argument(
        "--db-path",
        type=str,
        default=str(Path.home() / ".aichemist" / "relationships.db"),
        help="Path to the relationships database",
    )
    paths_parser.add_argument(
        "--output", type=Path, help="Output file for results (JSON)"
    )

    # Export visualization command
    export_parser = rel_subparsers.add_parser(
        "export", help="Export relationship graph visualization"
    )
    export_parser.add_argument(
        "output_path", help="Path to save the visualization file"
    )
    export_parser.add_argument(
        "--format", choices=["dot", "json"], default="json", help="Output format"
    )
    export_parser.add_argument(
        "--types",
        nargs="+",
        choices=[t.name for t in RelationshipType],
        help="Relationship types to include",
    )
    export_parser.add_argument(
        "--min-strength",
        type=float,
        default=0.0,
        help="Minimum relationship strength (0.0 to 1.0)",
    )
    export_parser.add_argument(
        "--max-nodes", type=int, default=100, help="Maximum number of nodes to include"
    )
    export_parser.add_argument(
        "--db-path",
        type=str,
        default=str(Path.home() / ".aichemist" / "relationships.db"),
        help="Path to the relationships database",
    )

    # Find central files command
    central_parser = rel_subparsers.add_parser(
        "find-central", help="Find the most central files in the codebase"
    )
    central_parser.add_argument(
        "--top-n", type=int, default=10, help="Number of top results to return"
    )
    central_parser.add_argument(
        "--types",
        nargs="+",
        choices=[t.name for t in RelationshipType],
        help="Relationship types to include",
    )
    central_parser.add_argument(
        "--min-strength",
        type=float,
        default=0.0,
        help="Minimum relationship strength (0.0 to 1.0)",
    )
    central_parser.add_argument(
        "--db-path",
        type=str,
        default=str(Path.home() / ".aichemist" / "relationships.db"),
        help="Path to the relationships database",
    )
    central_parser.add_argument(
        "--output", type=Path, help="Output file for results (JSON)"
    )
    # ---------------------------------------------------------

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

    elif args.command == "metadata":
        # Handle metadata extraction
        cache_manager = CacheManager()
        metadata_manager = MetadataManager(cache_manager)

        if args.metadata_command == "extract":
            file_path = args.file.resolve()
            output_file = args.output

            if not file_path.exists():
                logger.error(f"File does not exist: {file_path}")
                return

            logger.info(f"Extracting metadata from: {file_path}")

            # Extract metadata
            file_metadata = asyncio.run(metadata_manager.extract_metadata(file_path))

            # Convert metadata to dictionary
            metadata_dict = {
                k: v
                for k, v in vars(file_metadata).items()
                if not k.startswith("_") and v is not None
            }

            if output_file:
                asyncio.run(save_as_json_async(metadata_dict, output_file))
                logger.info(f"Metadata saved to {output_file}")
            else:
                # Print metadata in a readable format
                print(f"\nMetadata for {file_path}:")
                for key, value in metadata_dict.items():
                    if isinstance(value, (list, dict)) and value:
                        print(f"\n{key}:")
                        if isinstance(value, list):
                            for item in value:
                                print(f"  - {item}")
                        else:  # dict
                            for k, v in value.items():
                                print(f"  {k}: {v}")
                    elif value:
                        print(f"{key}: {value}")
                print()

        elif args.metadata_command == "batch":
            directory = args.directory
            output_file = args.output
            pattern = args.pattern or "*"
            max_concurrent = args.max_concurrent

            logger.info(f"Extracting metadata from files in: {directory}")

            # Get files to process
            if args.recursive:
                files = list(directory.glob(f"**/{pattern}"))
            else:
                files = list(directory.glob(pattern))

            if not files:
                logger.warning(
                    f"No files matching pattern '{pattern}' found in {directory}"
                )
                return

            logger.info(f"Found {len(files)} files to process")

            # Extract metadata in batch
            batch_results = asyncio.run(
                metadata_manager.extract_batch(files, max_concurrent=max_concurrent)
            )

            # Convert to dictionary format for output
            metadata_dicts = []
            for result in batch_results:
                metadata_dict = {
                    k: v
                    for k, v in vars(result).items()
                    if not k.startswith("_") and v is not None
                }
                metadata_dicts.append(metadata_dict)

            if output_file:
                asyncio.run(save_as_json_async(metadata_dicts, output_file))
                logger.info(f"Batch metadata saved to {output_file}")
            else:
                # Print summary
                print(f"\nExtracted metadata from {len(metadata_dicts)} files:")
                for i, metadata in enumerate(
                    metadata_dicts[:5], 1
                ):  # Show first 5 only
                    print(f"\n{i}. {metadata.get('path')}")
                    if metadata.get("tags"):
                        print(f"   Tags: {', '.join(metadata.get('tags'))}")
                    if metadata.get("mime_type"):
                        print(f"   Type: {metadata.get('mime_type')}")
                    if metadata.get("extraction_confidence"):
                        print(
                            f"   Confidence: {metadata.get('extraction_confidence'):.2f}"
                        )

                if len(metadata_dicts) > 5:
                    print(f"\n... and {len(metadata_dicts) - 5} more files")
                print()

        elif args.metadata_command == "analyze":
            directory = args.directory
            output_file = args.output
            group_by = args.group_by

            logger.info(f"Analyzing metadata in {directory}, grouping by {group_by}")

            # Get all files
            files = list(directory.glob("**/*"))
            files = [f for f in files if f.is_file()]

            if not files:
                logger.warning(f"No files found in {directory}")
                return

            logger.info(f"Found {len(files)} files to analyze")

            # Extract metadata in batch
            batch_results = asyncio.run(metadata_manager.extract_batch(files))

            # Group by the selected property
            groups = {}

            for result in batch_results:
                # Skip files with extraction errors
                if result.error:
                    continue

                if group_by == "tags" and hasattr(result, "tags") and result.tags:
                    # Group by tags (each file can belong to multiple groups)
                    for tag in result.tags:
                        if tag not in groups:
                            groups[tag] = []
                        groups[tag].append(str(result.path))

                elif group_by == "language":
                    # For code files
                    language = None
                    if hasattr(result, "code_language") and result.code_language:
                        language = result.code_language
                    # For text files
                    elif hasattr(result, "language") and result.language:
                        language = result.language
                    # Fallback to extension or mime type
                    else:
                        language = result.extension or result.mime_type.split("/")[0]

                    if language:
                        if language not in groups:
                            groups[language] = []
                        groups[language].append(str(result.path))

                elif group_by == "type":
                    # Group by MIME type main category
                    file_type = (
                        result.mime_type.split("/")[0]
                        if result.mime_type
                        else "unknown"
                    )
                    if file_type not in groups:
                        groups[file_type] = []
                    groups[file_type].append(str(result.path))

                elif (
                    group_by == "authors"
                    and hasattr(result, "authors")
                    and result.authors
                ):
                    # Group by authors
                    for author in result.authors:
                        if author not in groups:
                            groups[author] = []
                        groups[author].append(str(result.path))

            # Sort groups by size
            sorted_groups = sorted(
                groups.items(), key=lambda x: len(x[1]), reverse=True
            )

            # Format results
            analysis_results = {
                "group_by": group_by,
                "total_files": len(batch_results),
                "groups": {k: v for k, v in sorted_groups},
            }

            if output_file:
                asyncio.run(save_as_json_async(analysis_results, output_file))
                logger.info(f"Analysis results saved to {output_file}")
            else:
                # Print analysis results
                print(f"\nFile analysis by {group_by}:")
                print(f"Total files analyzed: {analysis_results['total_files']}")
                print(f"Found {len(analysis_results['groups'])} groups:")

                for group_name, files in list(analysis_results["groups"].items())[
                    :10
                ]:  # Show top 10
                    print(f"\n{group_name} ({len(files)} files)")
                    for file_path in files[:3]:  # Show first 3 files in each group
                        print(f"  - {file_path}")
                    if len(files) > 3:
                        print(f"  ... and {len(files) - 3} more")

                if len(analysis_results["groups"]) > 10:
                    print(
                        f"\n... and {len(analysis_results['groups']) - 10} more groups"
                    )
                print()

    elif args.command == "tags":
        # Initialize tag manager
        tag_db_path = Path.home() / ".aichemist" / "tags.db"
        tag_db_path.parent.mkdir(parents=True, exist_ok=True)

        async def handle_tags_command():
            async with TagManager(tag_db_path) as tag_manager:
                await tag_manager.initialize()

                # Get database connection for tag hierarchy
                conn = tag_manager.schema.get_connection()
                tag_hierarchy = TagHierarchy(conn)

                # Basic tag operations
                if args.tags_command == "add":
                    file_path = args.file.resolve()
                    if not file_path.exists():
                        logger.error(f"File not found: {file_path}")
                        return

                    logger.info(f"Adding tags to file: {file_path}")

                    added_count = 0
                    for tag_name in args.tags:
                        try:
                            # Check if tag exists, create if needed with description
                            tag = await tag_manager.get_tag_by_name(tag_name)
                            if not tag and args.description:
                                await tag_manager.create_tag(tag_name, args.description)

                            # Add tag to file
                            added = await tag_manager.add_file_tag(
                                file_path=file_path,
                                tag_name=tag_name,
                                source="manual",
                                confidence=1.0,
                            )
                            if added:
                                added_count += 1
                        except Exception as e:
                            logger.error(f"Error adding tag '{tag_name}': {e}")

                    logger.info(f"Added {added_count} tags to {file_path}")

                elif args.tags_command == "remove":
                    file_path = args.file.resolve()
                    if not file_path.exists():
                        logger.error(f"File not found: {file_path}")
                        return

                    logger.info(f"Removing tags from file: {file_path}")

                    removed_count = 0
                    for tag_name in args.tags:
                        try:
                            # Get tag ID
                            tag = await tag_manager.get_tag_by_name(tag_name)
                            if tag:
                                # Remove tag from file
                                removed = await tag_manager.remove_file_tag(
                                    file_path=file_path, tag_id=tag["id"]
                                )
                                if removed:
                                    removed_count += 1
                            else:
                                logger.warning(f"Tag not found: {tag_name}")
                        except Exception as e:
                            logger.error(f"Error removing tag '{tag_name}': {e}")

                    logger.info(f"Removed {removed_count} tags from {file_path}")

                elif args.tags_command == "list":
                    if args.file:
                        # List tags for a specific file
                        file_path = args.file.resolve()
                        if not file_path.exists():
                            logger.error(f"File not found: {file_path}")
                            return

                        logger.info(f"Listing tags for file: {file_path}")

                        # Get tags for the file
                        tags = await tag_manager.get_file_tags(file_path)

                        # Format results
                        result = {"file": str(file_path), "tags": []}

                        for tag in tags:
                            result["tags"].append(
                                {
                                    "name": tag["name"],
                                    "source": tag["source"],
                                    "confidence": tag["confidence"],
                                    "added_at": tag["added_at"],
                                }
                            )

                        # Output results
                        if args.output:
                            await save_as_json_async(result, args.output)
                            logger.info(f"Tags saved to {args.output}")
                        else:
                            print(f"\nTags for {file_path}:")
                            for tag in tags:
                                print(
                                    f"- {tag['name']} (confidence: {tag['confidence']:.2f}, source: {tag['source']})"
                                )
                            print()
                    else:
                        # List all tags
                        logger.info("Listing all tags")

                        # Get tag usage statistics
                        tag_stats = await tag_manager.get_tag_counts()

                        # Format results
                        result = {"tags": tag_stats}

                        # Output results
                        if args.output:
                            await save_as_json_async(result, args.output)
                            logger.info(f"Tags saved to {args.output}")
                        else:
                            print("\nAll tags:")
                            for tag in tag_stats:
                                print(f"- {tag['name']} ({tag['count']} files)")
                            print()

                elif args.tags_command == "suggest":
                    file_path = args.file.resolve()
                    if not file_path.exists():
                        logger.error(f"File not found: {file_path}")
                        return

                    logger.info(f"Suggesting tags for file: {file_path}")

                    # Create file reader and classifier
                    file_reader = FileReader()
                    classifier = TagClassifier()
                    tag_suggester = TagSuggester(tag_manager, classifier)

                    # Get file metadata
                    metadata = await file_reader.process_file(file_path)

                    # Get tag suggestions
                    suggestions = await tag_suggester.suggest_tags(
                        metadata, min_confidence=args.threshold
                    )

                    # Format results
                    result = {"file": str(file_path), "suggestions": []}

                    for tag, confidence in suggestions:
                        result["suggestions"].append(
                            {"tag": tag, "confidence": confidence}
                        )

                    # Apply suggested tags if requested
                    if args.apply and suggestions:
                        logger.info(f"Applying suggested tags to {file_path}")
                        added_count = await tag_manager.add_file_tags(
                            file_path=file_path, tags=suggestions, source="auto"
                        )
                        logger.info(f"Applied {added_count} tags")

                    # Output results
                    if args.output:
                        await save_as_json_async(result, args.output)
                        logger.info(f"Tag suggestions saved to {args.output}")
                    else:
                        print(f"\nSuggested tags for {file_path}:")
                        for tag, confidence in suggestions:
                            print(f"- {tag} (confidence: {confidence:.2f})")
                        print()

                elif args.tags_command == "batch":
                    directory = args.directory
                    recursive = args.recursive
                    pattern = args.pattern or "*"
                    threshold = args.threshold
                    apply_tags = args.apply

                    logger.info(f"Batch processing tags for files in: {directory}")

                    # Create classifier and suggester
                    classifier = TagClassifier()
                    tag_suggester = TagSuggester(tag_manager, classifier)

                    # Process directory
                    results = await tag_suggester.analyze_directory(
                        directory=directory,
                        recursive=recursive,
                        min_confidence=threshold,
                        apply_tags=apply_tags,
                    )

                    # Format results
                    result = {
                        "directory": str(directory),
                        "files_processed": len(results),
                        "results": {},
                    }

                    for file_path, suggestions in results.items():
                        result["results"][file_path] = [
                            {"tag": tag, "confidence": conf}
                            for tag, conf in suggestions
                        ]

                    # Output results
                    if args.output:
                        await save_as_json_async(result, args.output)
                        logger.info(f"Batch tag results saved to {args.output}")
                    else:
                        print(f"\nBatch tag results for {directory}:")
                        print(f"Processed {len(results)} files\n")
                        for file_path, suggestions in results.items():
                            if suggestions:
                                print(f"{file_path}:")
                                for tag, confidence in suggestions:
                                    print(f"  - {tag} (confidence: {confidence:.2f})")
                                print()

                elif args.tags_command == "find":
                    tags = args.tags
                    require_all = args.all
                    threshold = args.threshold

                    logger.info(f"Finding files with tags: {', '.join(tags)}")

                    # Get tag IDs
                    tag_ids = []
                    for tag_name in tags:
                        tag = await tag_manager.get_tag_by_name(tag_name)
                        if tag:
                            tag_ids.append(tag["id"])
                        else:
                            logger.warning(f"Tag not found: {tag_name}")

                    if not tag_ids:
                        logger.error("No valid tags specified")
                        return

                    # Find files with the specified tags
                    files = await tag_manager.get_files_by_tags(
                        tag_ids=tag_ids,
                        require_all=require_all,
                        min_confidence=threshold,
                    )

                    # Format results
                    result = {
                        "tags": tags,
                        "require_all": require_all,
                        "threshold": threshold,
                        "files": files,
                    }

                    # Output results
                    if args.output:
                        await save_as_json_async(result, args.output)
                        logger.info(f"File search results saved to {args.output}")
                    else:
                        tag_str = (
                            " AND ".join(tags) if require_all else " OR ".join(tags)
                        )
                        print(f"\nFiles with tags ({tag_str}):")
                        for file_path in files:
                            print(f"- {file_path}")
                        print(f"\nTotal: {len(files)} files\n")

                # Tag hierarchy operations
                elif args.tags_command == "hierarchy":
                    if args.hierarchy_command == "add":
                        parent_name = args.parent
                        child_name = args.child

                        logger.info(
                            f"Adding hierarchy relationship: {parent_name} -> {child_name}"
                        )

                        # Get or create the tags
                        parent_tag = await tag_manager.get_tag_by_name(parent_name)
                        if not parent_tag:
                            parent_id = await tag_manager.create_tag(parent_name)
                        else:
                            parent_id = parent_tag["id"]

                        child_tag = await tag_manager.get_tag_by_name(child_name)
                        if not child_tag:
                            child_id = await tag_manager.create_tag(child_name)
                        else:
                            child_id = child_tag["id"]

                        # Add the relationship
                        added = tag_hierarchy.add_relationship(parent_id, child_id)

                        if added:
                            print(
                                f"Added hierarchy relationship: {parent_name} -> {child_name}"
                            )
                        else:
                            print(
                                "Failed to add relationship (may already exist or would create a cycle)"
                            )

                    elif args.hierarchy_command == "remove":
                        parent_name = args.parent
                        child_name = args.child

                        logger.info(
                            f"Removing hierarchy relationship: {parent_name} -> {child_name}"
                        )

                        # Get the tags
                        parent_tag = await tag_manager.get_tag_by_name(parent_name)
                        child_tag = await tag_manager.get_tag_by_name(child_name)

                        if not parent_tag or not child_tag:
                            logger.error(
                                f"Tag not found: {parent_name if not parent_tag else child_name}"
                            )
                            return

                        # Remove the relationship
                        removed = tag_hierarchy.remove_relationship(
                            parent_tag["id"], child_tag["id"]
                        )

                        if removed:
                            print(
                                f"Removed hierarchy relationship: {parent_name} -> {child_name}"
                            )
                        else:
                            print(
                                f"Relationship not found: {parent_name} -> {child_name}"
                            )

                    elif args.hierarchy_command == "show":
                        if args.tag:
                            # Show hierarchy for a specific tag
                            tag_name = args.tag
                            tag = await tag_manager.get_tag_by_name(tag_name)

                            if not tag:
                                logger.error(f"Tag not found: {tag_name}")
                                return

                            logger.info(f"Showing hierarchy for tag: {tag_name}")

                            # Get hierarchy data
                            hierarchy = tag_hierarchy.export_taxonomy(tag["id"])

                            # Format results
                            result = {"tag": tag_name, "hierarchy": hierarchy}
                        else:
                            # Show entire hierarchy
                            logger.info("Showing complete tag hierarchy")

                            # Get hierarchy data
                            hierarchy = tag_hierarchy.export_taxonomy()

                            # Format results
                            result = {"hierarchy": hierarchy}

                        # Output results
                        if args.output:
                            await save_as_json_async(result, args.output)
                            logger.info(f"Hierarchy saved to {args.output}")
                        else:
                            print("\nTag Hierarchy:")
                            print(json.dumps(hierarchy, indent=2))
                            print()

                    elif args.hierarchy_command == "export":
                        output_file = args.output

                        logger.info(f"Exporting tag hierarchy to: {output_file}")

                        # Get complete hierarchy
                        hierarchy = tag_hierarchy.export_taxonomy()

                        # Save to file
                        await save_as_json_async(hierarchy, output_file)

                        logger.info(f"Hierarchy exported to {output_file}")

                    elif args.hierarchy_command == "import":
                        input_file = args.input

                        if not input_file.exists():
                            logger.error(f"Input file not found: {input_file}")
                            return

                        logger.info(f"Importing tag hierarchy from: {input_file}")

                        # Load hierarchy from file
                        with open(input_file, "r") as f:
                            hierarchy = json.load(f)

                        # Import the hierarchy
                        tag_map = tag_hierarchy.import_taxonomy(hierarchy)

                        logger.info(f"Imported hierarchy with {len(tag_map)} tags")

                # Classifier operations
                elif args.tags_command == "classifier":
                    if args.classifier_command == "train":
                        directory = args.directory
                        test_size = args.test_size

                        logger.info(f"Training tag classifier on files in: {directory}")

                        # Create classifier
                        classifier = TagClassifier()

                        # Get training data from tagged files
                        training_data = []

                        # Get all files in the directory
                        files = list(directory.glob("**/*"))
                        file_reader = FileReader()

                        logger.info(f"Found {len(files)} files to examine")

                        # Create training data from tagged files
                        for file_path in files:
                            if file_path.is_file():
                                try:
                                    # Get tags for this file
                                    tags = await tag_manager.get_file_tags(file_path)

                                    if tags:
                                        # Get tag names
                                        tag_names = [tag["name"] for tag in tags]

                                        # Get file metadata
                                        metadata = await file_reader.process_file(
                                            file_path
                                        )

                                        # Add to training data
                                        training_data.append((metadata, tag_names))

                                except Exception as e:
                                    logger.error(
                                        f"Error processing file {file_path}: {e}"
                                    )

                        if not training_data:
                            logger.error("No tagged files found for training")
                            return

                        logger.info(f"Training with {len(training_data)} tagged files")

                        # Train the classifier
                        results = await classifier.train(
                            training_data=training_data, test_size=test_size
                        )

                        # Show results
                        print("\nClassifier Training Results:")
                        print(f"Samples: {results['num_samples']}")
                        print(f"Tags: {results['num_tags']}")
                        print(f"Accuracy: {results['accuracy']:.4f}")
                        print(f"Training Date: {results['training_date']}")
                        print()

                    elif args.classifier_command == "info":
                        logger.info("Getting classifier information")

                        # Create classifier
                        classifier = TagClassifier()

                        # Get model info
                        info = await classifier.get_model_info()

                        # Format results
                        if args.output:
                            await save_as_json_async(info, args.output)
                            logger.info(f"Classifier info saved to {args.output}")
                        else:
                            print("\nTag Classifier Information:")
                            if info.get("num_tags", 0) > 0:
                                print(f"Tags: {info['num_tags']}")
                                print(f"Features: {info.get('num_features', 0)}")
                                print(f"Accuracy: {info.get('accuracy', 0):.4f}")
                                print(
                                    f"Last Updated: {info.get('last_updated', 'never')}"
                                )
                                print(
                                    f"Model Path: {info.get('model_path', 'not set')}"
                                )
                            else:
                                print("No trained model available")
                            print()

        asyncio.run(handle_tags_command())

    elif args.command == "relationships":
        # Initialize relationship store
        db_path = Path(
            args.db_path
            if hasattr(args, "db_path")
            else Path.home() / ".aichemist" / "relationships.db"
        )
        db_path.parent.mkdir(parents=True, exist_ok=True)

        async def handle_relationships_command():
            store = RelationshipStore(db_path)

            if args.rel_command == "detect":
                # Convert paths to Path objects
                paths = [Path(p) for p in args.paths]

                # Validate paths
                valid_paths = []
                for path in paths:
                    if path.exists():
                        valid_paths.append(path)
                    else:
                        logger.warning(f"Path does not exist: {path}")

                if not valid_paths:
                    logger.error("No valid paths to analyze")
                    return

                # Convert strategy names to enum values
                strategies = [DetectionStrategy[s] for s in args.strategies]

                # Create detector
                detector = RelationshipDetector()

                # Register available detectors
                workspace_root = Path.cwd()
                if DetectionStrategy.DIRECTORY_STRUCTURE.name in args.strategies:
                    directory_detector = DirectoryStructureDetector(
                        workspace_root=workspace_root
                    )
                    detector.register_detector(directory_detector)

                # TODO: Register additional detectors as they are implemented

                # Check if any detectors were registered
                if not detector._registered_detectors:
                    logger.warning(
                        "No detectors registered for selected strategies. Available strategies: "
                        + ", ".join(
                            [
                                s.name
                                for s in DetectionStrategy
                                if s != DetectionStrategy.ALL
                            ]
                        )
                    )
                    return

                # Define progress callback
                def progress_callback(current, total):
                    if total == 0:
                        return

                    progress = current / total
                    bar_length = 40
                    filled_length = int(bar_length * progress)

                    bar = "█" * filled_length + "░" * (bar_length - filled_length)
                    percent = progress * 100

                    sys.stdout.write(f"\r[{bar}] {percent:.1f}% ({current}/{total})")
                    sys.stdout.flush()

                    if current == total:
                        sys.stdout.write("\n")

                # Detect relationships
                logger.info(
                    f"Detecting relationships for {len(valid_paths)} files using strategies: {', '.join(args.strategies)}"
                )
                relationships = detector.detect_relationships(
                    valid_paths, strategies, progress_callback=progress_callback
                )

                # Store relationships
                store.add_relationships(relationships)

                logger.info(f"\nDetected and stored {len(relationships)} relationships")

            elif args.rel_command == "find-related":
                file_path = Path(args.file_path)

                if not file_path.exists():
                    logger.error(f"File does not exist: {file_path}")
                    return

                # Convert type names to enum values if specified
                rel_types = None
                if hasattr(args, "types") and args.types:
                    rel_types = [RelationshipType[t] for t in args.types]

                # Find related files
                related_files = store.get_related_files(
                    file_path, rel_types=rel_types, min_strength=args.min_strength
                )

                # Prepare results
                results = {
                    "file": str(file_path),
                    "related_files": [
                        {
                            "path": str(path),
                            "relationship_type": rel_type.name,
                            "strength": strength,
                        }
                        for path, rel_type, strength in related_files
                    ],
                }

                # Output results
                if hasattr(args, "output") and args.output:
                    with open(args.output, "w") as f:
                        json.dump(results, f, indent=2)
                    logger.info(f"Results saved to {args.output}")
                else:
                    if not related_files:
                        print(f"No related files found for {file_path}")
                    else:
                        print(f"\nFiles related to {file_path}:")
                        for path, rel_type, strength in related_files:
                            print(
                                f"  {path} ({rel_type.name}, strength: {strength:.2f})"
                            )

            elif args.rel_command == "find-paths":
                source_path = Path(args.source_path)
                target_path = Path(args.target_path)

                if not source_path.exists():
                    logger.error(f"Source file does not exist: {source_path}")
                    return

                if not target_path.exists():
                    logger.error(f"Target file does not exist: {target_path}")
                    return

                # Create graph
                graph = RelationshipGraph(store)

                # Find paths
                paths = graph.find_paths(
                    source_path, target_path, max_length=args.max_length
                )

                # Prepare results
                results = {
                    "source": str(source_path),
                    "target": str(target_path),
                    "paths": [
                        [
                            {"path": str(file_path), "relationship_type": rel_type.name}
                            for file_path, rel_type in path
                        ]
                        for path in paths
                    ],
                }

                # Output results
                if hasattr(args, "output") and args.output:
                    with open(args.output, "w") as f:
                        json.dump(results, f, indent=2)
                    logger.info(f"Results saved to {args.output}")
                else:
                    if not paths:
                        print(f"No paths found from {source_path} to {target_path}")
                    else:
                        print(f"\nPaths from {source_path} to {target_path}:")
                        for i, path in enumerate(paths, 1):
                            print(f"Path {i}:")
                            print(f"  {source_path}")
                            for file_path, rel_type in path:
                                print(f"  → {file_path} ({rel_type.name})")

            elif args.rel_command == "export":
                output_path = Path(args.output_path)

                # Convert type names to enum values if specified
                rel_types = None
                if hasattr(args, "types") and args.types:
                    rel_types = [RelationshipType[t] for t in args.types]

                # Create graph
                graph = RelationshipGraph(store)

                # Export graph
                try:
                    if args.format == "dot":
                        graph.export_graphviz(
                            output_path,
                            rel_types=rel_types,
                            min_strength=args.min_strength,
                            max_nodes=args.max_nodes,
                        )
                    else:  # json
                        graph.export_json(
                            output_path,
                            rel_types=rel_types,
                            min_strength=args.min_strength,
                            max_nodes=args.max_nodes,
                        )

                    logger.info(f"Exported relationship graph to {output_path}")
                except Exception as e:
                    logger.error(f"Error exporting graph: {str(e)}")

            elif args.rel_command == "find-central":
                # Create graph
                graph = RelationshipGraph(store)

                # Convert type names to enum values if specified
                rel_types = None
                if hasattr(args, "types") and args.types:
                    rel_types = [RelationshipType[t] for t in args.types]

                # Calculate centrality
                central_files = graph.calculate_centrality(
                    rel_types=rel_types,
                    min_strength=args.min_strength,
                    top_n=args.top_n,
                )

                # Prepare results
                results = {
                    "central_files": [
                        {"path": str(path), "centrality_score": score}
                        for path, score in central_files
                    ]
                }

                # Output results
                if hasattr(args, "output") and args.output:
                    with open(args.output, "w") as f:
                        json.dump(results, f, indent=2)
                    logger.info(f"Results saved to {args.output}")
                else:
                    if not central_files:
                        print("No central files found")
                    else:
                        print(f"\nTop {len(central_files)} most central files:")
                        for path, score in central_files:
                            print(f"  {path} (score: {score:.4f})")

        asyncio.run(handle_relationships_command())

    # ✅ Other commands (ingest, notebooks, etc.)
    # ... existing code ...


if __name__ == "__main__":
    main()
