"""Command-line interface for The Aichemist Codex."""

import argparse
import asyncio
import json
import logging
import sqlite3
import sys
from pathlib import Path

from the_aichemist_codex.backend.file_manager.duplicate_detector import (
    DuplicateDetector,
)
from the_aichemist_codex.backend.file_manager.file_tree import FileTreeGenerator
from the_aichemist_codex.backend.file_manager.file_watcher import FileEventHandler
from the_aichemist_codex.backend.file_manager.sorter import RuleBasedSorter
from the_aichemist_codex.backend.file_reader.file_reader import FileReader
from the_aichemist_codex.backend.ingest.aggregator import aggregate_digest
from the_aichemist_codex.backend.ingest.scanner import scan_directory
from the_aichemist_codex.backend.metadata.manager import MetadataManager
from the_aichemist_codex.backend.output_formatter.json_writer import save_as_json_async
from the_aichemist_codex.backend.output_formatter.markdown_writer import (
    save_as_markdown,
)
from the_aichemist_codex.backend.project_reader.code_summary import summarize_project
from the_aichemist_codex.backend.project_reader.notebooks import NotebookConverter
from the_aichemist_codex.backend.project_reader.token_counter import TokenAnalyzer
from the_aichemist_codex.backend.relationships.detector import (
    DetectionStrategy,
    RelationshipDetector,
)
from the_aichemist_codex.backend.relationships.detectors.directory_structure import (
    DirectoryStructureDetector,
)
from the_aichemist_codex.backend.relationships.graph import RelationshipGraph
from the_aichemist_codex.backend.relationships.relationship import RelationshipType
from the_aichemist_codex.backend.relationships.store import RelationshipStore
from the_aichemist_codex.backend.rollback.rollback_manager import RollbackManager
from the_aichemist_codex.backend.search.search_engine import SearchEngine
from the_aichemist_codex.backend.tagging.classifier import TagClassifier
from the_aichemist_codex.backend.tagging.hierarchy import TagHierarchy
from the_aichemist_codex.backend.tagging.manager import TagManager
from the_aichemist_codex.backend.tagging.suggester import TagSuggester
from the_aichemist_codex.backend.utils.cache_manager import CacheManager

logger = logging.getLogger(__name__)


def validate_directory(directory: str) -> Path:
    """Ensure the given directory exists and is accessible."""
    path = Path(directory)
    resolved_dir = path.resolve()
    if not resolved_dir.exists() or not resolved_dir.is_dir():
        raise argparse.ArgumentTypeError(f"Directory does not exist: {resolved_dir}")
    return resolved_dir


def main() -> None:
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

    sort_parser = subparsers.add_parser(
        "sort", help="Sort files according to defined rules."
    )
    sort_parser.add_argument(
        "directory", type=validate_directory, help="Directory to sort."
    )
    sort_parser.add_argument(
        "--config", type=Path, help="Path to custom sorting rules YAML file."
    )
    sort_parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Run in dry-run mode (no files will be moved). This is TRUE by default for safety.",
    )
    sort_parser.add_argument(
        "--confirm",
        action="store_false",
        dest="dry_run",
        help="Actually perform the file operations (override dry-run).",
    )
    sort_parser.add_argument(
        "--backup",
        action="store_true",
        default=True,
        help="Create backups of all files before moving them. Default is True.",
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

    # Add notification commands
    notification_parser = subparsers.add_parser(
        "notify", help="Manage system notifications."
    )
    notification_subparsers = notification_parser.add_subparsers(
        dest="notify_command", required=True
    )

    # List notifications command
    list_parser = notification_subparsers.add_parser("list", help="List notifications")
    list_parser.add_argument(
        "--type", dest="notification_type", help="Filter by notification type"
    )
    list_parser.add_argument("--level", help="Filter by minimum notification level")
    list_parser.add_argument(
        "--limit", type=int, default=20, help="Maximum number of notifications to show"
    )
    list_parser.add_argument(
        "--format",
        dest="format_output",
        choices=["table", "json"],
        default="table",
        help="Output format",
    )

    # Show notification command
    show_parser = notification_subparsers.add_parser(
        "show", help="Show notification details"
    )
    show_parser.add_argument("id", help="Notification ID")
    show_parser.add_argument(
        "--format",
        dest="format_output",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )

    # Send notification command
    send_parser = notification_subparsers.add_parser("send", help="Send a notification")
    send_parser.add_argument("message", help="Notification message")
    send_parser.add_argument(
        "--level",
        default="INFO",
        help="Notification level (INFO, WARNING, ERROR, CRITICAL)",
    )
    send_parser.add_argument(
        "--type", dest="notification_type", default="SYSTEM", help="Notification type"
    )
    send_parser.add_argument(
        "--source", default="cli", help="Source of the notification"
    )
    send_parser.add_argument(
        "--details", type=json.loads, help="Additional details (JSON format)"
    )

    # Cleanup command
    cleanup_parser = notification_subparsers.add_parser(
        "cleanup", help="Clean up old notifications"
    )
    cleanup_parser.add_argument(
        "--days",
        type=float,
        help="Number of days to keep (default: use configured value)",
    )

    # Rule management commands
    rule_parser = notification_subparsers.add_parser(
        "rule", help="Manage notification rules"
    )
    rule_subparsers = rule_parser.add_subparsers(dest="rule_command", required=True)

    # List rules command
    rule_list_parser = rule_subparsers.add_parser(
        "list", help="List all notification rules"
    )
    rule_list_parser.add_argument(
        "--format",
        dest="format_output",
        choices=["table", "json"],
        default="table",
        help="Output format",
    )

    # Show rule command
    rule_show_parser = rule_subparsers.add_parser(
        "show", help="Show details of a specific rule"
    )
    rule_show_parser.add_argument("id", help="Rule ID")
    rule_show_parser.add_argument(
        "--format",
        dest="format_output",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )

    # Add rule command
    rule_add_parser = rule_subparsers.add_parser(
        "add", help="Add a new notification rule"
    )
    rule_add_parser.add_argument(
        "--file",
        type=Path,
        required=True,
        help="Path to JSON file containing rule definition",
    )

    # Update rule command
    rule_update_parser = rule_subparsers.add_parser(
        "update", help="Update an existing notification rule"
    )
    rule_update_parser.add_argument("id", help="Rule ID to update")
    rule_update_parser.add_argument(
        "--file",
        type=Path,
        required=True,
        help="Path to JSON file containing updated rule definition",
    )

    # Delete rule command
    rule_delete_parser = rule_subparsers.add_parser(
        "delete", help="Delete a notification rule"
    )
    rule_delete_parser.add_argument("id", help="Rule ID to delete")

    # Enable/disable rule command
    rule_toggle_parser = rule_subparsers.add_parser(
        "toggle", help="Enable or disable a notification rule"
    )
    rule_toggle_parser.add_argument("id", help="Rule ID to toggle")
    rule_toggle_parser.add_argument(
        "--enable", type=bool, required=True, help="True to enable, False to disable"
    )

    # Test rule command
    rule_test_parser = rule_subparsers.add_parser(
        "test", help="Test a rule against a notification"
    )
    rule_test_parser.add_argument("id", help="Rule ID to test")
    rule_test_parser.add_argument(
        "--message", required=True, help="Notification message"
    )
    rule_test_parser.add_argument(
        "--level",
        default="INFO",
        help="Notification level (INFO, WARNING, ERROR, CRITICAL)",
    )
    rule_test_parser.add_argument(
        "--type", dest="notification_type", default="SYSTEM", help="Notification type"
    )
    rule_test_parser.add_argument(
        "--source", default="test", help="Source of the notification"
    )
    rule_test_parser.add_argument(
        "--details", type=json.loads, help="Additional details (JSON format)"
    )

    # Add data directory management commands
    data_parser = subparsers.add_parser(
        "data", help="Manage data directories and files."
    )
    data_subparsers = data_parser.add_subparsers(dest="data_command", required=True)

    # Validate command
    data_validate_parser = data_subparsers.add_parser(
        "validate", help="Validate the data directory structure."
    )

    # Repair command
    data_repair_parser = data_subparsers.add_parser(
        "repair",
        help="Repair the data directory structure by creating missing components.",
    )

    # Info command
    data_info_parser = data_subparsers.add_parser(
        "info", help="Show information about data directories."
    )

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
        asyncio.run(
            summarize_project(
                args.directory,
                output_md_file,
                output_json_file,
            )
        )
        if args.output_format == "json":
            logger.info(f"Code summary saved to {output_json_file}")
        elif args.output_format == "md":
            logger.info(f"Markdown summary saved to {output_md_file}")

    elif args.command == "sort":
        logger.info(f"Sorting files in {args.directory}")
        sorter = RuleBasedSorter()

        # If a config file was provided, use it
        if args.config and args.config.exists():
            logger.info(f"Using sorting rules from: {args.config}")
            sorter.config_file = args.config

        # Add dry run option
        if args.dry_run:
            logger.info("Running in dry-run mode - no files will be moved")

            # Create a custom sort method for dry run
            async def dry_run_sort(directory: Path) -> None:
                rules = await sorter.load_rules()
                for file in directory.rglob("*"):
                    if file.is_file():
                        for rule in rules:
                            if await sorter.rule_matches_extended(file, rule):
                                target_dir_value = rule.get("target_dir")
                                if target_dir_value is None:
                                    continue  # Skip rule if no target directory specified
                                target_dir = Path(target_dir_value)
                                if not target_dir.is_absolute():
                                    target_dir = directory / target_dir
                                target_file = target_dir / file.name
                                if rule.get("preserve_path", False):
                                    rel_path = file.relative_to(directory)
                                    if len(rel_path.parts) > 1:
                                        parent_dir = rel_path.parts[0]
                                        new_filename = f"{parent_dir}_{file.name}"
                                        target_file = target_dir / new_filename
                                logger.info(f"Would move: {file} -> {target_file}")
                                break

            asyncio.run(dry_run_sort(args.directory))
        else:
            sorter.sort_directory_sync(args.directory)

        logger.info("File sorting completed")

    elif args.command == "duplicates":
        output_file = args.output or args.directory / "duplicates.json"
        logger.info(f"Scanning for duplicates in {args.directory}")
        duplicate_detector = DuplicateDetector()
        duplicates_dict = asyncio.run(
            duplicate_detector.scan_directory(args.directory, method=args.method)
        )
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

        # Implement directory scanning since TokenAnalyzer only has estimate method
        token_counts = {}
        for file_path in args.directory.glob("**/*.txt"):
            try:
                with open(file_path, encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                token_counts[str(file_path)] = token_analyzer.estimate(content)
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")

        asyncio.run(save_as_json_async(token_counts, output_file))
        logger.info(f"Token counts saved to {output_file}")

    elif args.command == "search":
        output_file = args.output
        logger.info(f"Searching for '{args.query}' in {args.directory}")

        # Initialize search engine with cache manager for better performance
        cache_manager = CacheManager()
        search_engine = SearchEngine(args.directory, cache_manager=cache_manager)

        # Check if database is empty and index files if needed
        if args.method == "regex":
            logger.info(f"Performing regex search with pattern: {args.query}")

            # Get all files in the directory
            include_patterns = {"*"}
            ignore_patterns = set()
            files = scan_directory(args.directory, include_patterns, ignore_patterns)

            # Convert to Path objects
            file_paths = [Path(f) for f in files]
            logger.info(f"Found {len(file_paths)} files to search through")

            # Perform regex search directly on files
            results = asyncio.run(
                search_engine.regex_search_async(
                    args.query,
                    file_paths=file_paths,
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

        # Create a content map for the files
        content_map = {}
        for file_path in files:
            try:
                with open(file_path, encoding="utf-8", errors="ignore") as f:
                    content_map[file_path] = f.read()
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}")

        content = aggregate_digest(files, content_map)
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
        mime_type = reader.get_mime_type(args.file)
        metadata = asyncio.run(reader.process_file(args.file))
        content = metadata.preview
        if args.format == "auto":
            print(content)
        elif args.format == "json":
            if args.output:
                metadata_dict = {
                    k: v
                    for k, v in vars(metadata).items()
                    if not k.startswith("_") and v is not None
                }
                asyncio.run(save_as_json_async(metadata_dict, args.output))
                logger.info(f"JSON output saved to {args.output}")
            else:
                print(content)
        elif args.format == "markdown":
            if args.output:
                # Create dummy data structure expected by save_as_markdown
                data = {str(args.file): {"summary": content, "functions": []}}
                asyncio.run(save_as_markdown(Path(args.output), data))
                logger.info(f"Markdown output saved to {args.output}")
            else:
                # Create a minimal representation for display
                print(f"# {args.file.name}\n\n{content}")
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

            # Use safer file writing approach with platform-specific handling
            try:
                import platform

                system = platform.system()

                # Windows approach (default)
                if system == "Windows":
                    try:
                        # Try to use Windows file locking
                        with open(rm.rollback_log, "w") as f:
                            try:
                                import msvcrt

                                # Lock file for writing
                                msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
                            except (OSError, ImportError):
                                # If locking fails, we'll still try to update the file
                                logger.warning(
                                    "File locking not available on this Windows system"
                                )

                            try:
                                # Write empty array
                                json.dump([], f, indent=4)
                            finally:
                                # Unlock file if locked
                                try:
                                    import msvcrt

                                    # Unlock the file
                                    f.seek(
                                        0
                                    )  # Need to be at the beginning for unlocking
                                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                                except (OSError, ImportError):
                                    pass
                    except Exception as e:
                        logger.error(f"Error clearing rollback log on Windows: {e}")
                        # Fallback to simple write
                        with open(rm.rollback_log, "w") as f:
                            json.dump([], f, indent=4)
                # Unix approach (fallback) - COMMENTED OUT
                else:
                    # Simple non-locking approach since Unix code is commented out
                    with open(rm.rollback_log, "w") as f:
                        json.dump([], f, indent=4)

                    # COMMENTED OUT: Unix-specific code
                    """
                    try:
                        import fcntl

                        # Safely write an empty array to the rollback log file
                        with open(rm.rollback_log, "w") as f:
                            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                            try:
                                json.dump([], f, indent=4)
                            finally:
                                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                    except ImportError:
                        # fcntl not available, use simple write
                        logger.warning(
                            "fcntl not available on this system, using simple file write"
                        )
                        with open(rm.rollback_log, "w") as f:
                            json.dump([], f, indent=4)
                    """

                logger.info("Cleared all rollback operations.")
            except Exception as e:
                logger.error(f"Error clearing rollback log: {e}")

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
                    # For code files - use direct attribute access based on FileMetadata class
                    language = None
                    # Use language or programming_language attribute from FileMetadata
                    if hasattr(result, "language") and result.language:
                        language = result.language
                    elif (
                        hasattr(result, "programming_language")
                        and result.programming_language
                    ):
                        language = result.programming_language
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
                    and hasattr(result, "author")
                    and result.author
                ):
                    # Group by author - use the author attribute from FileMetadata
                    author = result.author
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
                "groups": dict(sorted_groups),
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

        async def handle_tags_command() -> None:
            # Import json inside the async function to ensure it's in scope
            import json

            async with TagManager(tag_db_path) as tag_manager:
                await tag_manager.initialize()

                # Create direct connection for tag hierarchy
                conn = sqlite3.connect(str(tag_db_path))
                conn.row_factory = sqlite3.Row
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
                    classifier = TagClassifier(Path.home() / ".aichemist" / "models")
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
                    classifier = TagClassifier(Path.home() / ".aichemist" / "models")
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
                        with open(input_file) as f:
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
                        classifier = TagClassifier(
                            Path.home() / ".aichemist" / "models"
                        )

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
                        classifier = TagClassifier(
                            Path.home() / ".aichemist" / "models"
                        )

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

        async def handle_relationships_command() -> None:
            # Import json inside the async function to ensure it's in scope
            import json

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
                def progress_callback(current: int, total: int) -> None:
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

    # Handle notification commands
    elif args.command == "notify":

        async def handle_notify_command() -> None:
            if args.notify_command == "list":
                await list_notifications(
                    notification_type=args.notification_type,
                    level=args.level,
                    limit=args.limit,
                    format_output=args.format_output,
                )
            elif args.notify_command == "show":
                await show_notification(
                    notification_id=args.id,
                    format_output=args.format_output,
                )
            elif args.notify_command == "send":
                await send_notification(
                    message=args.message,
                    level=args.level,
                    notification_type=args.notification_type,
                    source=args.source,
                    details=args.details,
                )
            elif args.notify_command == "cleanup":
                await cleanup_notifications(days=args.days)
            elif args.notify_command == "rule":
                # Handle rule management commands
                if args.rule_command == "list":
                    await list_rules(format_output=args.format_output)
                elif args.rule_command == "show":
                    await show_rule(rule_id=args.id, format_output=args.format_output)
                elif args.rule_command == "add":
                    await add_rule(rule_file=args.file)
                elif args.rule_command == "update":
                    await update_rule(rule_id=args.id, rule_file=args.file)
                elif args.rule_command == "delete":
                    await delete_rule(rule_id=args.id)
                elif args.rule_command == "toggle":
                    await toggle_rule(rule_id=args.id, enable=args.enable)
                elif args.rule_command == "test":
                    await test_rule(
                        rule_id=args.id,
                        message=args.message,
                        level=args.level,
                        notification_type=args.notification_type,
                        source=args.source,
                        details=args.details,
                    )

        # Import the notification functions - fix the import path
        from the_aichemist_codex.backend.notification import (
            Notification,
            NotificationLevel,
            NotificationType,
            notification_manager,
        )

        # Import the rule engine
        try:
            from the_aichemist_codex.backend.notification.rule_engine import (
                NotificationRule,
                RuleAction,
                RuleCondition,
                TimeCondition,
                rule_engine,
            )

            has_rule_engine = True
        except ImportError:
            has_rule_engine = False
            print("Warning: Rule engine not available.")

        # Define the notification CLI functions right here instead of importing
        async def list_notifications(
            notification_type: str | None = None,
            level: str | None = None,
            limit: int = 20,
            format_output: str = "table",
        ) -> None:
            """List notifications from the database."""
            import json
            from datetime import datetime

            from tabulate import tabulate

            # Get notifications
            notifications = await notification_manager.get_notifications(
                notification_type=notification_type,
                level=level,
                limit=limit,
            )

            if not notifications:
                print("No notifications found.")
                return

            if format_output == "json":
                print(json.dumps(notifications, indent=2))
                return

            # Format as table
            headers = ["ID", "Level", "Type", "Source", "Time", "Message"]
            rows = []

            for notification in notifications:
                # Format timestamp
                timestamp = datetime.fromtimestamp(notification["timestamp"]).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                # Add row
                rows.append(
                    [
                        notification["id"],
                        notification["level"],
                        notification["type"],
                        notification["source"] or "-",
                        timestamp,
                        notification["message"][:50]
                        + ("..." if len(notification["message"]) > 50 else ""),
                    ]
                )

            print(tabulate(rows, headers=headers, tablefmt="pretty"))
            print(f"\nTotal: {len(notifications)} notifications")

        async def show_notification(
            notification_id: str, format_output: str = "text"
        ) -> None:
            """Show details of a specific notification."""
            import json
            from datetime import datetime

            notification = await notification_manager.get_notification_by_id(
                notification_id
            )

            if not notification:
                print(f"Notification with ID '{notification_id}' not found.")
                return

            if format_output == "json":
                print(json.dumps(notification, indent=2))
                return

            # Format as text
            timestamp = datetime.fromtimestamp(notification["timestamp"]).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            print(f"ID:       {notification['id']}")
            print(f"Level:    {notification['level']}")
            print(f"Type:     {notification['type']}")
            print(f"Source:   {notification['source'] or '-'}")
            print(f"Time:     {timestamp}")
            print(f"Message:  {notification['message']}")

            if notification.get("details"):
                print("\nDetails:")
                for key, value in notification["details"].items():
                    print(f"  {key}: {value}")

        async def send_notification(
            message: str,
            level: str = "INFO",
            notification_type: str = "SYSTEM",
            source: str = "cli",
            details: dict | None = None,
        ) -> None:
            """Send a notification."""
            # Validate level
            try:
                level_enum = NotificationLevel.from_string(level)
            except (ValueError, KeyError):
                print(f"Invalid notification level: {level}")
                print(f"Valid levels: {', '.join(nl.name for nl in NotificationLevel)}")
                return

            # Validate type
            try:
                if notification_type.upper() in (nt.name for nt in NotificationType):
                    type_enum = getattr(NotificationType, notification_type.upper())
                else:
                    type_enum = NotificationType(notification_type.lower())
            except (ValueError, KeyError):
                print(f"Invalid notification type: {notification_type}")
                print(f"Valid types: {', '.join(nt.name for nt in NotificationType)}")
                return

            # Send notification
            notification_id = await notification_manager.notify(
                message=message,
                level=level_enum,
                notification_type=type_enum,
                source=source,
                details=details,
            )

            if notification_id:
                print(f"Notification sent with ID: {notification_id}")
            else:
                print("Failed to send notification (possibly throttled).")

        async def cleanup_notifications(days: int | None = None) -> None:
            """Clean up old notifications."""
            removed = await notification_manager.cleanup()
            print(f"Removed {removed} old notifications.")

        # Define rule management CLI functions
        async def list_rules(format_output: str = "table") -> None:
            """List all notification rules."""
            if not has_rule_engine:
                print("Rule engine not available.")
                return

            import json

            from tabulate import tabulate

            # Get all rules
            rules = await rule_engine.get_all_rules()

            if not rules:
                print("No rules found.")
                return

            if format_output == "json":
                print(json.dumps(rules, indent=2))
                return

            # Format as table
            headers = [
                "ID",
                "Name",
                "Priority",
                "Enabled",
                "Conditions",
                "Actions",
                "Matches",
            ]
            rows = []

            for rule in rules:
                # Format for table
                rows.append(
                    [
                        rule["rule_id"],
                        rule["name"],
                        rule["priority"],
                        "✓" if rule["enabled"] else "✗",
                        len(rule["conditions"]),
                        len(rule["actions"]),
                        rule["stats"].get("match_count", 0),
                    ]
                )

            print(tabulate(rows, headers=headers, tablefmt="pretty"))
            print(f"\nTotal: {len(rules)} rules")

        async def show_rule(rule_id: str, format_output: str = "text") -> None:
            """Show details of a specific rule."""
            if not has_rule_engine:
                print("Rule engine not available.")
                return

            import json
            from datetime import datetime

            # Get the rule
            rule = await rule_engine.get_rule(rule_id)

            if not rule:
                print(f"Rule with ID '{rule_id}' not found.")
                return

            rule_dict = rule.to_dict()

            if format_output == "json":
                print(json.dumps(rule_dict, indent=2))
                return

            # Format as text
            print(f"ID:          {rule_dict['rule_id']}")
            print(f"Name:        {rule_dict['name']}")
            print(f"Description: {rule_dict['description']}")
            print(f"Priority:    {rule_dict['priority']}")
            print(f"Enabled:     {rule_dict['enabled']}")
            print(f"Subscribers: {rule_dict['subscribers'] or 'All'}")

            last_match = rule_dict["stats"].get("last_match_time")
            match_count = rule_dict["stats"].get("match_count", 0)
            if last_match:
                last_match_time = datetime.fromtimestamp(last_match).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                print(f"Matches:     {match_count} (last: {last_match_time})")
            else:
                print(f"Matches:     {match_count}")

            print("\nConditions:")
            if not rule_dict["conditions"]:
                print("  None")
            else:
                for i, condition in enumerate(rule_dict["conditions"], 1):
                    op = "NOT " if condition["negate"] else ""
                    print(
                        f"  {i}. {condition['field']} {op}{condition['operator']} {condition['value']}"
                    )

            if rule_dict.get("time_conditions"):
                print("\nTime Conditions:")
                for i, condition in enumerate(rule_dict["time_conditions"], 1):
                    print(f"  {i}. {condition['condition_type']}: {condition['value']}")

            print("\nActions:")
            if not rule_dict["actions"]:
                print("  None")
            else:
                for i, action in enumerate(rule_dict["actions"], 1):
                    print(f"  {i}. {action['action_type']}")
                    for param, value in action["parameters"].items():
                        print(f"     - {param}: {value}")

        async def add_rule(rule_file: str) -> None:
            """Add a new notification rule from a JSON file."""
            if not has_rule_engine:
                print("Rule engine not available.")
                return

            import json

            try:
                # Read the rule definition from the file
                with open(rule_file) as f:
                    rule_data = json.load(f)

                # Create rule
                rule = NotificationRule(
                    name=rule_data["name"],
                    description=rule_data["description"],
                    conditions=[
                        RuleCondition.from_dict(c) for c in rule_data["conditions"]
                    ],
                    time_conditions=[
                        TimeCondition.from_dict(tc)
                        for tc in rule_data.get("time_conditions", [])
                    ]
                    if rule_data.get("time_conditions")
                    else None,
                    actions=[
                        RuleAction.from_dict(a) for a in rule_data.get("actions", [])
                    ]
                    if rule_data.get("actions")
                    else None,
                    enabled=rule_data.get("enabled", True),
                    priority=rule_data.get("priority", 100),
                    subscribers=rule_data.get("subscribers"),
                )

                # Add the rule
                rule_id = await rule_engine.add_rule(rule)
                print(f"Rule added with ID: {rule_id}")

            except Exception as e:
                print(f"Error adding rule: {e}")

        async def update_rule(rule_id: str, rule_file: str) -> None:
            """Update an existing rule from a JSON file."""
            if not has_rule_engine:
                print("Rule engine not available.")
                return

            import json

            # Check if rule exists
            rule = await rule_engine.get_rule(rule_id)
            if not rule:
                print(f"Rule with ID '{rule_id}' not found.")
                return

            try:
                # Read the rule definition from the file
                with open(rule_file) as f:
                    rule_data = json.load(f)

                # Create updated rule (preserving ID)
                updated_rule = NotificationRule(
                    name=rule_data["name"],
                    description=rule_data["description"],
                    conditions=[
                        RuleCondition.from_dict(c) for c in rule_data["conditions"]
                    ],
                    time_conditions=[
                        TimeCondition.from_dict(tc)
                        for tc in rule_data.get("time_conditions", [])
                    ]
                    if rule_data.get("time_conditions")
                    else None,
                    actions=[
                        RuleAction.from_dict(a) for a in rule_data.get("actions", [])
                    ]
                    if rule_data.get("actions")
                    else None,
                    enabled=rule_data.get("enabled", True),
                    priority=rule_data.get("priority", 100),
                    subscribers=rule_data.get("subscribers"),
                    rule_id=rule_id,  # Preserve the original rule ID
                )

                # Update the rule
                success = await rule_engine.update_rule(updated_rule)
                if success:
                    print(f"Rule '{rule_id}' updated successfully.")
                else:
                    print(f"Failed to update rule '{rule_id}'.")

            except Exception as e:
                print(f"Error updating rule: {e}")

        async def delete_rule(rule_id: str) -> None:
            """Delete a notification rule."""
            if not has_rule_engine:
                print("Rule engine not available.")
                return

            # Delete the rule
            success = await rule_engine.delete_rule(rule_id)
            if success:
                print(f"Rule '{rule_id}' deleted successfully.")
            else:
                print(f"Rule with ID '{rule_id}' not found.")

        async def toggle_rule(rule_id: str, enable: bool) -> None:
            """Enable or disable a notification rule."""
            if not has_rule_engine:
                print("Rule engine not available.")
                return

            # Get the rule
            rule = await rule_engine.get_rule(rule_id)
            if not rule:
                print(f"Rule with ID '{rule_id}' not found.")
                return

            # Update enabled status
            rule.enabled = enable
            success = await rule_engine.update_rule(rule)

            if success:
                status = "enabled" if enable else "disabled"
                print(f"Rule '{rule_id}' {status} successfully.")
            else:
                print(f"Failed to update rule '{rule_id}'.")

        async def test_rule(
            rule_id: str,
            message: str,
            level: str,
            notification_type: str,
            source: str,
            details: dict | None,
        ) -> None:
            """Test a rule against a notification."""
            if not has_rule_engine:
                print("Rule engine not available.")
                return

            # Get the rule
            rule = await rule_engine.get_rule(rule_id)
            if not rule:
                print(f"Rule with ID '{rule_id}' not found.")
                return

            # Create a test notification
            notification = Notification(
                message=message,
                level=level,
                notification_type=notification_type,
                source=source,
                details=details or {},
            )

            # Simulate the rule
            result = await rule_engine.simulate_rule(rule, notification)

            # Display results
            print(f"Rule: {result['rule']['name']}")
            print(f"Matches: {'Yes' if result['matches'] else 'No'}")

            if result["matches"]:
                print("\nActions:")
                if result["would_block"]:
                    print("- Would BLOCK the notification")

                if result["would_route_to"]:
                    print(f"- Would ROUTE to: {', '.join(result['would_route_to'])}")

                if result["would_throttle"]:
                    print(f"- Would apply THROTTLING: {result['would_throttle']}")

                if (
                    result["notification_after"]
                    and result["notification_after"] != result["notification_before"]
                ):
                    print("\nNotification would be modified:")
                    print("Before:")
                    for k, v in result["notification_before"].items():
                        print(f"  {k}: {v}")
                    print("After:")
                    for k, v in result["notification_after"].items():
                        print(f"  {k}: {v}")

        # Run the command handler
        asyncio.run(handle_notify_command())

    elif args.command == "data":
        # Handle data directory management commands
        if args.data_command == "validate":
            # Validate the data directory structure
            from the_aichemist_codex.backend.config import settings
            from the_aichemist_codex.backend.utils.validate_data_dir import (
                get_directory_status,
            )

            overall_status, validation, issues = get_directory_status()

            if overall_status:
                print("✓ Data directory structure is valid")
                print(f"Base directory: {settings.DATA_DIR}")
            else:
                print("✗ Data directory structure has issues:")
                for issue in issues:
                    print(f"  - {issue}")

            # Print detailed status
            print("\nDetailed status:")
            print(f"{'Component':<25} {'Status':<10} {'Path'}")
            print("-" * 80)

            for component, status in validation.items():
                if component == "base":
                    path = settings.DATA_DIR
                elif component in settings.directory_manager.STANDARD_DIRS:
                    path = settings.directory_manager.get_dir(component)
                else:
                    path = settings.directory_manager.get_file_path(component)

                status_text = "✓ Valid" if status else "✗ Missing"
                print(f"{component:<25} {status_text:<10} {path}")

        elif args.data_command == "repair":
            # Repair the data directory structure
            from the_aichemist_codex.backend.utils.validate_data_dir import (
                get_directory_status,
                repair_data_directory,
            )

            # Repair the directory
            fixes = repair_data_directory()

            if fixes:
                print("Applied the following fixes:")
                for fix in fixes:
                    print(f"  - {fix}")
            else:
                print("✓ No repairs needed, data directory structure is valid")

            # Validate again to confirm
            overall_status, _, _ = get_directory_status()
            if overall_status:
                print("✓ Data directory structure is now valid")
            else:
                print("✗ Some issues could not be fixed automatically")

        elif args.data_command == "info":
            # Show information about data directories

            from the_aichemist_codex.backend.config import settings
            from the_aichemist_codex.backend.utils.validate_data_dir import (
                get_directory_status,
            )

            print("Data Directory Information")
            print(f"Base directory: {settings.DATA_DIR}")

            # Print directory sizes
            print("\nDirectory Sizes:")
            print(f"{'Directory':<15} {'Size':<10} {'Items'}")
            print("-" * 50)

            # Add base directory
            try:
                base_size = sum(
                    f.stat().st_size
                    for f in settings.DATA_DIR.glob("**/*")
                    if f.is_file()
                )
                base_item_count = sum(1 for _ in settings.DATA_DIR.glob("**/*"))
                print(
                    f"{'Base':<15} {base_size / (1024 * 1024):.2f} MB  {base_item_count}"
                )
            except Exception as e:
                print(f"{'Base':<15} Error: {e}")

            # Add subdirectories
            for subdir in settings.directory_manager.STANDARD_DIRS:
                dir_path = settings.directory_manager.get_dir(subdir)
                if dir_path.exists():
                    try:
                        size = sum(
                            f.stat().st_size
                            for f in dir_path.glob("**/*")
                            if f.is_file()
                        )
                        item_count = sum(1 for _ in dir_path.glob("**/*"))
                        print(
                            f"{subdir:<15} {size / (1024 * 1024):.2f} MB  {item_count}"
                        )
                    except Exception as e:
                        print(f"{subdir:<15} Error: {e}")
                else:
                    print(f"{subdir:<15} Not found  -")

            # Print environment variables
            print("\nEnvironment Variables:")
            print(f"{'Variable':<20} {'Value':<30} {'Status'}")
            print("-" * 70)

            env_vars = {
                "AICHEMIST_DATA_DIR": "Override base data directory",
                "AICHEMIST_ROOT_DIR": "Override project root directory",
                "AICHEMIST_CACHE_DIR": "Override cache directory",
            }

            for var, description in env_vars.items():
                value = os.environ.get(var, "")
                if value:
                    path = Path(value)
                    status = "Exists" if path.exists() else "Not found"
                    print(f"{var:<20} {value:<30} {status}")
                else:
                    print(f"{var:<20} Not set  -")

    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
