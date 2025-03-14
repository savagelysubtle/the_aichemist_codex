"""
CLI commands for the relationship mapping feature.

This module provides command-line interface commands for detecting,
querying, and visualizing file relationships.
"""

import logging
import sys
from pathlib import Path

from backend.relationships.detector import DetectionStrategy, RelationshipDetector
from backend.relationships.graph import RelationshipGraph
from backend.relationships.relationship import RelationshipType
from backend.relationships.store import RelationshipStore

logger = logging.getLogger(__name__)


def setup_relationship_commands(subparsers):
    """
    Set up the relationship mapping CLI commands.

    Args:
        subparsers: Subparsers object from argparse
    """
    # Detect relationships command
    detect_parser = subparsers.add_parser(
        "detect-relationships", help="Detect relationships between files"
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
        default=".relationships.db",
        help="Path to the relationships database",
    )
    detect_parser.set_defaults(func=detect_relationships_command)

    # Find related files command
    related_parser = subparsers.add_parser(
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
        default=".relationships.db",
        help="Path to the relationships database",
    )
    related_parser.set_defaults(func=find_related_command)

    # Find paths between files command
    paths_parser = subparsers.add_parser(
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
        default=".relationships.db",
        help="Path to the relationships database",
    )
    paths_parser.set_defaults(func=find_paths_command)

    # Export visualization command
    export_parser = subparsers.add_parser(
        "export-graph", help="Export relationship graph visualization"
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
        default=".relationships.db",
        help="Path to the relationships database",
    )
    export_parser.set_defaults(func=export_graph_command)

    # Find central files command
    central_parser = subparsers.add_parser(
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
        default=".relationships.db",
        help="Path to the relationships database",
    )
    central_parser.set_defaults(func=find_central_command)


def detect_relationships_command(args):
    """
    Detect relationships between files.

    Args:
        args: Command-line arguments
    """
    # Convert paths to Path objects
    paths = [Path(p) for p in args.paths]

    # Convert strategy names to enum values
    strategies = [DetectionStrategy[s] for s in args.strategies]

    # Create detector and store
    detector = RelationshipDetector()
    store = RelationshipStore(Path(args.db_path))

    # TODO: Register actual detectors
    # This is a placeholder - in a real implementation, we would
    # register the appropriate detectors based on the selected strategies

    # Detect relationships
    print(f"Detecting relationships for {len(paths)} files...")
    relationships = detector.detect_relationships(
        paths, strategies, progress_callback=_progress_callback
    )

    # Store relationships
    store.add_relationships(relationships)

    print(f"\nDetected {len(relationships)} relationships.")


def find_related_command(args):
    """
    Find files related to a specific file.

    Args:
        args: Command-line arguments
    """
    file_path = Path(args.file_path)

    # Convert type names to enum values if specified
    rel_types = None
    if args.types:
        rel_types = [RelationshipType[t] for t in args.types]

    # Create store
    store = RelationshipStore(Path(args.db_path))

    # Find related files
    related_files = store.get_related_files(
        file_path, rel_types=rel_types, min_strength=args.min_strength
    )

    # Display results
    if not related_files:
        print(f"No related files found for {file_path}")
        return

    print(f"Files related to {file_path}:")
    for path, rel_type, strength in related_files:
        print(f"  {path} ({rel_type.name}, strength: {strength:.2f})")


def find_paths_command(args):
    """
    Find paths between two files.

    Args:
        args: Command-line arguments
    """
    source_path = Path(args.source_path)
    target_path = Path(args.target_path)

    # Create store and graph
    store = RelationshipStore(Path(args.db_path))
    graph = RelationshipGraph(store)

    # Find paths
    paths = graph.find_paths(source_path, target_path, max_length=args.max_length)

    # Display results
    if not paths:
        print(f"No paths found from {source_path} to {target_path}")
        return

    print(f"Paths from {source_path} to {target_path}:")
    for i, path in enumerate(paths, 1):
        print(f"Path {i}:")
        print(f"  {source_path}")
        for file_path, rel_type in path:
            print(f"  → {file_path} ({rel_type.name})")


def export_graph_command(args):
    """
    Export relationship graph visualization.

    Args:
        args: Command-line arguments
    """
    output_path = Path(args.output_path)

    # Convert type names to enum values if specified
    rel_types = None
    if args.types:
        rel_types = [RelationshipType[t] for t in args.types]

    # Create store and graph
    store = RelationshipStore(Path(args.db_path))
    graph = RelationshipGraph(store)

    # Export graph
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

    print(f"Exported relationship graph to {output_path}")


def find_central_command(args):
    """
    Find the most central files in the codebase.

    Args:
        args: Command-line arguments
    """
    # Convert type names to enum values if specified
    rel_types = None
    if args.types:
        rel_types = [RelationshipType[t] for t in args.types]

    # Create store and graph
    store = RelationshipStore(Path(args.db_path))
    graph = RelationshipGraph(store)

    # Calculate centrality
    central_files = graph.calculate_centrality(
        rel_types=rel_types, min_strength=args.min_strength, top_n=args.top_n
    )

    # Display results
    if not central_files:
        print("No central files found")
        return

    print(f"Top {len(central_files)} most central files:")
    for path, score in central_files:
        print(f"  {path} (score: {score:.4f})")


def _progress_callback(current: int, total: int) -> None:
    """
    Callback for reporting progress during relationship detection.

    Args:
        current: Current progress value
        total: Total progress value
    """
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
