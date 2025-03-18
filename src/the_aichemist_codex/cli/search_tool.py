"""
Command-line interface for searching content.

This module provides a CLI tool for searching content using the
AIChemist Codex search engine, with support for different search modes.
"""

import argparse
import asyncio
import logging
import sys

from the_aichemist_codex.backend.bootstrap import initialize_application_async
from the_aichemist_codex.backend.core.exceptions import AiChemistError

logger = logging.getLogger(__name__)


async def search(
    query: str,
    provider: str | None = None,
    max_results: int = 10,
    threshold: float = 0.5,
    case_sensitive: bool = False,
    content_types: list[str] | None = None,
    output_format: str = "text",
    include_content: bool = False,
) -> None:
    """
    Perform a search and print results.

    Args:
        query: Search query
        provider: Search provider to use (text, regex, vector, or None for all)
        max_results: Maximum number of results to return
        threshold: Minimum score threshold (0-1)
        case_sensitive: Whether to use case-sensitive search (for text/regex)
        content_types: List of content types to filter by
        output_format: Output format (text or json)
        include_content: Whether to include content in results
    """
    try:
        # Initialize application
        registry = await initialize_application_async(enable_logging=False)

        # Get search engine
        search_engine = registry.search_engine

        # Prepare search options
        options = {
            "max_results": max_results,
            "threshold": threshold,
            "case_sensitive": case_sensitive,
            "include_content": include_content,
        }

        if content_types:
            options["content_types"] = content_types

        # Perform search
        results = await search_engine.search(query, provider, options)

        # Output results
        if output_format == "json":
            import json

            print(json.dumps(results, indent=2))
        else:
            print(f"Search results for '{query}':")
            print(f"Found {len(results)} results\n")

            for i, result in enumerate(results, 1):
                print(f"Result {i}:")
                print(f"  Score: {result.get('score', 0):.4f}")
                print(f"  File: {result.get('file', {}).get('path', 'N/A')}")
                print(f"  Title: {result.get('file', {}).get('name', 'N/A')}")

                if "match_context" in result:
                    print(f"  Context: {result.get('match_context', '')}")

                if include_content and "content" in result:
                    print(f"  Content: {result.get('content', '')[:200]}...")

                print()

    except AiChemistError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


async def index_file(file_path: str, providers: list[str] | None = None) -> None:
    """
    Index a file for searching.

    Args:
        file_path: Path to the file to index
        providers: Search providers to use (text, regex, vector, or None for all)
    """
    try:
        # Initialize application
        registry = await initialize_application_async(enable_logging=False)

        # Get index manager
        index_manager = registry.index_manager

        # Index file
        results = await index_manager.index_file(file_path, providers)

        # Output results
        print(f"Indexed file: {file_path}")
        for provider, success in results.items():
            status = "Success" if success else "Failed"
            print(f"  {provider}: {status}")

    except AiChemistError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


async def index_directory(
    directory_path: str,
    recursive: bool = True,
    providers: list[str] | None = None,
    file_types: list[str] | None = None,
) -> None:
    """
    Index a directory for searching.

    Args:
        directory_path: Path to the directory to index
        recursive: Whether to recursively index subdirectories
        providers: Search providers to use (text, regex, vector, or None for all)
        file_types: File types to index (e.g., ".txt", ".py")
    """
    try:
        # Initialize application
        registry = await initialize_application_async(enable_logging=False)

        # Get index manager
        index_manager = registry.index_manager

        # Index directory
        results = await index_manager.index_directory(
            directory_path, recursive, providers, file_types
        )

        # Output results
        print(f"Indexed directory: {directory_path}")
        print(f"Recursive: {'Yes' if recursive else 'No'}")

        if file_types:
            print(f"File types: {', '.join(file_types)}")

        for provider, stats in results.items():
            print(f"\nProvider: {provider}")
            print(f"  Successful: {stats.get('success', 0)}")
            print(f"  Failed: {stats.get('failed', 0)}")
            print(f"  Skipped: {stats.get('skipped', 0)}")

    except AiChemistError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


async def get_search_stats() -> None:
    """Get statistics about the search system."""
    try:
        # Initialize application
        registry = await initialize_application_async(enable_logging=False)

        # Get search engine and index manager
        search_engine = registry.search_engine
        index_manager = registry.index_manager

        # Get provider information
        providers = await search_engine.list_providers()

        # Get index statistics
        stats = await index_manager.get_index_stats()

        # Output provider information
        print("Search Providers:")
        for provider in providers:
            default_indicator = " (default)" if provider.get("is_default") else ""
            print(f"  {provider.get('id')}: {provider.get('type')}{default_indicator}")

        # Output index statistics
        print("\nIndex Statistics:")
        for provider_id, provider_stats in stats.items():
            print(f"\nProvider: {provider_id}")

            if isinstance(provider_stats, dict):
                for key, value in provider_stats.items():
                    print(f"  {key}: {value}")
            else:
                print(f"  {provider_stats}")

    except AiChemistError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point for the search CLI tool."""
    parser = argparse.ArgumentParser(description="AIChemist Codex Search Tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search for content")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "--provider", "-p", help="Search provider (text, regex, vector)"
    )
    search_parser.add_argument(
        "--max-results", "-m", type=int, default=10, help="Maximum number of results"
    )
    search_parser.add_argument(
        "--threshold",
        "-t",
        type=float,
        default=0.5,
        help="Minimum score threshold (0-1)",
    )
    search_parser.add_argument(
        "--case-sensitive", "-c", action="store_true", help="Case-sensitive search"
    )
    search_parser.add_argument(
        "--content-types", "-ct", nargs="+", help="Content types to search"
    )
    search_parser.add_argument(
        "--output-format",
        "-o",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    search_parser.add_argument(
        "--include-content",
        "-i",
        action="store_true",
        help="Include content in results",
    )

    # Index file command
    index_file_parser = subparsers.add_parser("index-file", help="Index a file")
    index_file_parser.add_argument("file_path", help="Path to file")
    index_file_parser.add_argument(
        "--providers", "-p", nargs="+", help="Search providers to use"
    )

    # Index directory command
    index_dir_parser = subparsers.add_parser("index-dir", help="Index a directory")
    index_dir_parser.add_argument("directory_path", help="Path to directory")
    index_dir_parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        default=True,
        help="Recursively index subdirectories",
    )
    index_dir_parser.add_argument(
        "--providers", "-p", nargs="+", help="Search providers to use"
    )
    index_dir_parser.add_argument(
        "--file-types", "-f", nargs="+", help="File types to index (e.g., .txt, .py)"
    )

    # Stats command
    subparsers.add_parser("stats", help="Get search statistics")

    args = parser.parse_args()

    if args.command == "search":
        asyncio.run(
            search(
                args.query,
                args.provider,
                args.max_results,
                args.threshold,
                args.case_sensitive,
                args.content_types,
                args.output_format,
                args.include_content,
            )
        )
    elif args.command == "index-file":
        asyncio.run(index_file(args.file_path, args.providers))
    elif args.command == "index-dir":
        asyncio.run(
            index_directory(
                args.directory_path, args.recursive, args.providers, args.file_types
            )
        )
    elif args.command == "stats":
        asyncio.run(get_search_stats())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
