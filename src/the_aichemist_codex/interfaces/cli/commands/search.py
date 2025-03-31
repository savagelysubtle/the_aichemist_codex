"""Search commands for the AIchemist Codex CLI.

This module provides commands for searching files and content in the codebase
using various search methods including filename, fuzzy, semantic, regex, and full-text.
"""

import asyncio
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from the_aichemist_codex.infrastructure.ai.search.search_engine import SearchEngine
from the_aichemist_codex.infrastructure.fs.file_metadata import FileMetadata
from the_aichemist_codex.infrastructure.utils.cache_manager import CacheManager

console = Console()
search_app = typer.Typer(help="Search files and content")

# Store reference to CLI instance
_cli = None


def register_commands(app: Any, cli: Any) -> None:
    """Register search commands with the application."""
    global _cli
    _cli = cli
    app.add_typer(search_app, name="search")


@search_app.command("files")
def search_files(
    query: str = typer.Argument(..., help="Search query"),
    method: str = typer.Option(
        "fuzzy",
        "--method",
        "-m",
        help="Search method (fuzzy, filename, fulltext, semantic)",
    ),
    case_sensitive: bool = typer.Option(
        False, "--case-sensitive", "-c", help="Enable case-sensitive search"
    ),
    threshold: float = typer.Option(
        80.0, "--threshold", "-t", help="Match threshold (0-100)"
    ),
    max_results: int = typer.Option(20, "--max", "-n", help="Maximum results to show"),
    index_dir: str = typer.Option(
        "./.aichemist/search_index", help="Directory for search index"
    ),
) -> None:
    """
    Search for files by name or content.

    Examples:
        aichemist search files config
        aichemist search files "import numpy" --method fulltext
        aichemist search files user --method fuzzy --threshold 60
        aichemist search files "authentication flow" --method semantic
    """
    try:
        # Create index directory if it doesn't exist
        index_path = Path(index_dir)
        index_path.mkdir(parents=True, exist_ok=True)

        # Create cache manager
        cache_manager = CacheManager()

        # Initialize search engine
        search_engine = SearchEngine(
            index_dir=index_path,
            db_path=index_path / "search.db",
            cache_manager=cache_manager,
        )

        # Show a spinner during search
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Searching..."),
            transient=True,
        ) as progress:
            progress.add_task("search", total=None)

            # Execute search based on the method
            if method == "fuzzy":
                results = asyncio.run(
                    search_engine.fuzzy_search_async(query, threshold)
                )
                result_type = "Fuzzy Search"
            elif method == "filename":
                results = asyncio.run(search_engine.search_filename_async(query))
                result_type = "Filename Search"
            elif method == "fulltext":
                results = search_engine.full_text_search(query)
                result_type = "Full-text Search"
            elif method == "semantic":
                results = asyncio.run(
                    search_engine.semantic_search_async(query, max_results)
                )
                result_type = "Semantic Search"
            else:
                raise ValueError(f"Unknown search method: {method}")

        # Display results
        if not results:
            console.print("[yellow]No results found.[/]")
            return

        # Create a table for results
        table = Table(show_header=True, header_style="bold")
        table.add_column("#", style="dim", width=4)
        table.add_column("Path")

        # Limit results
        if len(results) > max_results:
            results = results[:max_results]

        # Add rows to table
        for i, path in enumerate(results, 1):
            table.add_row(str(i), str(path))

        # Display results
        console.print(
            f"\n[bold green]{result_type}[/] results for '[bold]{escape(query)}[/]':"
        )
        console.print(table)
        console.print(f"Found [bold]{len(results)}[/] results")

    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error:[/] {str(e)}")


@search_app.command("regex")
def regex_search(
    pattern: str = typer.Argument(..., help="Regex pattern to search for"),
    path: str = typer.Option(
        ".", "--path", "-p", help="Directory or file to search in"
    ),
    case_sensitive: bool = typer.Option(
        False, "--case-sensitive", "-c", help="Enable case-sensitive search"
    ),
    whole_word: bool = typer.Option(
        False, "--whole-word", "-w", help="Match whole words only"
    ),
    max_results: int = typer.Option(20, "--max", "-n", help="Maximum results to show"),
    index_dir: str = typer.Option(
        "./.aichemist/search_index", help="Directory for search index"
    ),
) -> None:
    """
    Search for regex patterns in file contents.

    Examples:
        aichemist search regex "import.*numpy"
        aichemist search regex r"class\s+\w+" --path ./src --case-sensitive
        aichemist search regex "function" --whole-word
    """
    try:
        # Create index directory if it doesn't exist
        index_path = Path(index_dir)
        index_path.mkdir(parents=True, exist_ok=True)

        # Create cache manager
        cache_manager = CacheManager()

        # Initialize search engine
        search_engine = SearchEngine(
            index_dir=index_path,
            db_path=index_path / "search.db",
            cache_manager=cache_manager,
        )

        # Resolve the search path
        search_path = Path(path).resolve()
        if not search_path.exists():
            raise FileNotFoundError(f"Path not found: {search_path}")

        # Prepare file paths
        file_paths: list[Path] = []
        if search_path.is_dir():
            # Collect all text files in the directory
            for item in search_path.rglob("*"):
                if item.is_file() and not item.name.startswith("."):
                    file_paths.append(item)
        else:
            file_paths = [search_path]

        # Show a spinner during search
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Searching with regex..."),
            transient=True,
        ) as progress:
            progress.add_task("search", total=None)

            # Execute regex search
            results = asyncio.run(
                search_engine.regex_search_async(
                    pattern=pattern,
                    file_paths=file_paths,
                    case_sensitive=case_sensitive,
                    whole_word=whole_word,
                )
            )

        # Display results
        if not results:
            console.print("[yellow]No results found.[/]")
            return

        # Create a table for results
        table = Table(show_header=True, header_style="bold")
        table.add_column("#", style="dim", width=4)
        table.add_column("Path")

        # Limit results
        if len(results) > max_results:
            results = results[:max_results]

        # Add rows to table
        for i, path in enumerate(results, 1):
            table.add_row(str(i), str(path))

        # Display results
        console.print(
            f"\n[bold green]Regex Search[/] results for '[bold]{escape(pattern)}[/]':"
        )
        console.print(table)
        console.print(f"Found [bold]{len(results)}[/] results")

    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error:[/] {str(e)}")


@search_app.command("similar")
def find_similar(
    file: str = typer.Argument(..., help="File to find similar files for"),
    threshold: float = typer.Option(
        0.7, "--threshold", "-t", help="Similarity threshold (0.0-1.0)"
    ),
    max_results: int = typer.Option(10, "--max", "-n", help="Maximum results to show"),
    index_dir: str = typer.Option(
        "./.aichemist/search_index", help="Directory for search index"
    ),
):
    """
    Find files similar to the given file.

    Examples:
        aichemist search similar src/main.py
        aichemist search similar src/utils/helpers.py --threshold 0.8
        aichemist search similar src/models/user.py --max 15
    """
    try:
        # Create index directory if it doesn't exist
        index_path = Path(index_dir)
        index_path.mkdir(parents=True, exist_ok=True)

        # Create cache manager
        cache_manager = CacheManager()

        # Initialize search engine
        search_engine = SearchEngine(
            index_dir=index_path,
            db_path=index_path / "search.db",
            cache_manager=cache_manager,
        )

        # Resolve the file path
        file_path = Path(file).resolve()
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        if not file_path.is_file():
            raise ValueError(f"Not a file: {file_path}")

        # Show a spinner during search
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Finding similar files..."),
            transient=True,
        ) as progress:
            progress.add_task("search", total=None)

            # Execute similarity search
            results = asyncio.run(
                search_engine.find_similar_files_async(
                    file_path=file_path,
                    threshold=threshold,
                    max_results=max_results,
                )
            )

        # Display results
        if not results:
            console.print("[yellow]No similar files found.[/]")
            return

        # Create a table for results
        table = Table(show_header=True, header_style="bold")
        table.add_column("#", style="dim", width=4)
        table.add_column("Path")
        table.add_column("Score", justify="right")

        # Add rows to table
        for i, result in enumerate(results, 1):
            path = result["path"]
            score = result["score"]
            table.add_row(str(i), str(path), f"{float(score):.2f}")

        # Display results
        console.print(
            f"\n[bold green]Similar Files[/] to '[bold]{escape(str(file_path))}[/]':"
        )
        console.print(table)
        console.print(f"Found [bold]{len(results)}[/] similar files")

    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error:[/] {str(e)}")


@search_app.command("index")
def index_files(
    path: str = typer.Argument(".", help="Directory or file to index"),
    recursive: bool = typer.Option(
        True, "--recursive/--no-recursive", help="Index directories recursively"
    ),
    batch_size: int = typer.Option(
        20, "--batch-size", "-b", help="Batch size for indexing"
    ),
    index_dir: str = typer.Option(
        "./.aichemist/search_index", help="Directory for search index"
    ),
):
    """
    Index files for searching.

    Examples:
        aichemist search index ./src
        aichemist search index ./docs --no-recursive
        aichemist search index ./src --batch-size 50
    """
    try:
        # Create index directory if it doesn't exist
        index_path = Path(index_dir)
        index_path.mkdir(parents=True, exist_ok=True)

        # Create cache manager
        cache_manager = CacheManager()

        # Initialize search engine
        search_engine = SearchEngine(
            index_dir=index_path,
            db_path=index_path / "search.db",
            cache_manager=cache_manager,
        )

        # Resolve the path
        target_path = Path(path).resolve()
        if not target_path.exists():
            raise FileNotFoundError(f"Path not found: {target_path}")

        # Collect files for indexing
        files_to_index = []

        if target_path.is_file():
            # Single file
            files_to_index.append(target_path)
        else:
            # Directory
            pattern = "**/*" if recursive else "*"
            for item in target_path.glob(pattern):
                if item.is_file() and not item.name.startswith("."):
                    files_to_index.append(item)

        if not files_to_index:
            console.print("[yellow]No files found to index.[/]")
            return

        # Create file metadata objects
        metadata_list = []
        for file_path in files_to_index:
            try:
                # Create a simple metadata object
                metadata = FileMetadata(
                    path=file_path,
                    mime_type="",  # Will be determined during indexing
                    size=file_path.stat().st_size,
                    extension=file_path.suffix,
                    preview="",  # Will be read during indexing
                )
                metadata_list.append(metadata)
            except Exception as e:
                console.print(
                    f"[yellow]Warning:[/] Cannot create metadata for {file_path}: {e}"
                )

        # Show progress during indexing
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Indexing files..."),
            transient=False,
        ) as progress:
            progress.add_task("index", total=None)

            # Execute batch indexing
            indexed_files = asyncio.run(
                search_engine.add_to_index_batch(
                    file_metadata_list=metadata_list, batch_size=batch_size
                )
            )

        # Display results
        if not indexed_files:
            console.print("[yellow]No files were indexed successfully.[/]")
            return

        console.print(
            f"[bold green]Successfully indexed [bold]{len(indexed_files)}[/] out of [bold]{len(files_to_index)}[/] files."
        )

    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error:[/] {str(e)}")


@search_app.command("groups")
def find_groups(
    path: str = typer.Argument(".", help="Directory to find file groups in"),
    threshold: float = typer.Option(
        0.7, "--threshold", "-t", help="Similarity threshold (0.0-1.0)"
    ),
    min_size: int = typer.Option(2, "--min-size", "-m", help="Minimum group size"),
    index_dir: str = typer.Option(
        "./.aichemist/search_index", help="Directory for search index"
    ),
):
    """
    Find groups of similar files.

    Examples:
        aichemist search groups ./src
        aichemist search groups ./src --threshold 0.8 --min-size 3
    """
    try:
        # Create index directory if it doesn't exist
        index_path = Path(index_dir)
        index_path.mkdir(parents=True, exist_ok=True)

        # Create cache manager
        cache_manager = CacheManager()

        # Initialize search engine
        search_engine = SearchEngine(
            index_dir=index_path,
            db_path=index_path / "search.db",
            cache_manager=cache_manager,
        )

        # Resolve the path
        target_path = Path(path).resolve()
        if not target_path.exists():
            raise FileNotFoundError(f"Path not found: {target_path}")
        if not target_path.is_dir():
            raise ValueError(f"Not a directory: {target_path}")

        # Collect files
        file_paths = []
        for item in target_path.rglob("*"):
            if item.is_file() and not item.name.startswith("."):
                file_paths.append(item)

        if not file_paths:
            console.print("[yellow]No files found for grouping.[/]")
            return

        # Show a spinner during search
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Finding file groups..."),
            transient=True,
        ) as progress:
            progress.add_task("search", total=None)

            # Execute group finding
            groups = asyncio.run(
                search_engine.find_file_groups_async(
                    file_paths=file_paths,
                    threshold=threshold,
                    min_group_size=min_size,
                )
            )

        # Display results
        if not groups:
            console.print("[yellow]No file groups found.[/]")
            return

        # Display each group
        console.print(
            f"\n[bold green]Found {len(groups)} file groups[/] with similarity threshold {threshold} and minimum size {min_size}:"
        )

        for i, group in enumerate(groups, 1):
            panel = Panel(
                "\n".join([f"[cyan]{path}[/]" for path in group]),
                title=f"Group {i} ({len(group)} files)",
                title_align="left",
                border_style="green",
            )
            console.print(panel)

    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error:[/] {str(e)}")
