"""Tagging commands for the AIchemist Codex CLI.

This module provides commands for working with file tags, including adding, removing,
listing, and suggesting tags as well as managing tag hierarchies.
"""

import asyncio
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from the_aichemist_codex.domain.tagging import TagManager
from the_aichemist_codex.domain.tagging.suggester import TagSuggester
from the_aichemist_codex.infrastructure.fs.file_metadata import FileMetadata
from the_aichemist_codex.infrastructure.fs.file_reader import FileReader

console = Console()
tagging_app = typer.Typer(help="Manage file tags and tag hierarchies")

# Store reference to CLI instance
_cli = None
# Store reference to tag manager
_tag_manager = None
# Default database path
_db_path = Path.home() / ".aichemist" / "tags.db"


def register_commands(app: Any, cli: Any) -> None:
    """Register tagging commands with the application."""
    global _cli, _tag_manager, _db_path
    _cli = cli

    # Set database path based on CLI config if available
    if hasattr(cli, "config") and cli.config:
        config_db_path = getattr(cli.config, "tags_db_path", None)
        if config_db_path:
            _db_path = Path(config_db_path)

    # Ensure the database directory exists
    _db_path.parent.mkdir(parents=True, exist_ok=True)

    app.add_typer(tagging_app, name="tag")


def get_tag_manager() -> TagManager:
    """Get or create tag manager instance."""
    global _tag_manager, _db_path
    if _tag_manager is None:
        _tag_manager = TagManager(_db_path)
    return _tag_manager


@tagging_app.command("add")
def add_tag(
    path: str = typer.Argument(..., help="Path to file or directory"),
    tags: list[str] = typer.Argument(..., help="Tags to add"),
    recursive: bool = typer.Option(
        False, "--recursive", "-r", help="Apply to all files in directory recursively"
    ),
) -> None:
    """
    Add tags to files.

    Examples:
        aichemist tag add path/to/file.py python backend
        aichemist tag add path/to/dir -r frontend
    """
    try:
        # Get tag manager
        tag_manager = get_tag_manager()

        # Initialize tag manager
        asyncio.run(tag_manager.initialize())

        # Resolve the file or directory path
        target_path = Path(path).resolve()

        if not target_path.exists():
            raise FileNotFoundError(f"Path not found: {target_path}")

        files_to_tag = []

        # Handle directory with recursive option
        if target_path.is_dir():
            if recursive:
                console.print(
                    f"Scanning directory [bold]{target_path}[/] recursively..."
                )
                files_to_tag.extend(
                    [
                        f
                        for f in target_path.rglob("*")
                        if f.is_file() and not f.name.startswith(".")
                    ]
                )
            else:
                console.print(f"Scanning directory [bold]{target_path}[/]...")
                files_to_tag.extend(
                    [
                        f
                        for f in target_path.glob("*")
                        if f.is_file() and not f.name.startswith(".")
                    ]
                )
        else:
            # Single file
            files_to_tag.append(target_path)

        # If no files found
        if not files_to_tag:
            console.print("[yellow]No files found to tag.[/]")
            return

        # Add tags with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Adding tags..."),
            transient=True,
        ) as progress:
            task = progress.add_task("add_tags", total=len(files_to_tag))

            count = 0
            for file in files_to_tag:
                for tag in tags:
                    asyncio.run(tag_manager.add_file_tag(file, tag_name=tag))
                count += 1
                progress.update(task, advance=1)

        console.print(
            f"[bold green]✓[/] Added tags {', '.join(f'[bold]{t}[/]' for t in tags)} to {count} files"
        )

    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error:[/] {str(e)}")


@tagging_app.command("remove")
def remove_tag(
    path: str = typer.Argument(..., help="Path to file or directory"),
    tags: list[str] = typer.Argument(..., help="Tags to remove"),
    recursive: bool = typer.Option(
        False, "--recursive", "-r", help="Apply to all files in directory recursively"
    ),
    all_tags: bool = typer.Option(
        False, "--all", "-a", help="Remove all tags from the specified files"
    ),
) -> None:
    """
    Remove tags from files.

    Examples:
        aichemist tag remove path/to/file.py python backend
        aichemist tag remove path/to/dir -r --all
    """
    try:
        # Get tag manager
        tag_manager = get_tag_manager()

        # Initialize tag manager
        asyncio.run(tag_manager.initialize())

        # Resolve the file or directory path
        target_path = Path(path).resolve()

        if not target_path.exists():
            raise FileNotFoundError(f"Path not found: {target_path}")

        files_to_untag = []

        # Handle directory with recursive option
        if target_path.is_dir():
            if recursive:
                console.print(
                    f"Scanning directory [bold]{target_path}[/] recursively..."
                )
                files_to_untag.extend(
                    [
                        f
                        for f in target_path.rglob("*")
                        if f.is_file() and not f.name.startswith(".")
                    ]
                )
            else:
                console.print(f"Scanning directory [bold]{target_path}[/]...")
                files_to_untag.extend(
                    [
                        f
                        for f in target_path.glob("*")
                        if f.is_file() and not f.name.startswith(".")
                    ]
                )
        else:
            # Single file
            files_to_untag.append(target_path)

        # If no files found
        if not files_to_untag:
            console.print("[yellow]No files found.[/]")
            return

        # Remove tags with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Removing tags..."),
            transient=True,
        ) as progress:
            task = progress.add_task("remove_tags", total=len(files_to_untag))

            async def process_file_tags():
                count = 0
                for file in files_to_untag:
                    file_path_str = str(file.resolve())
                    if all_tags:
                        # First, get all tags for the file
                        file_tags = await tag_manager.get_file_tags(file)
                        # Then remove each tag
                        for tag_info in file_tags:
                            await tag_manager.remove_file_tag(file, tag_info["id"])
                    else:
                        # Remove specific tags
                        for tag_name in tags:
                            # Get tag ID first
                            tag = await tag_manager.get_tag_by_name(tag_name)
                            if tag:
                                await tag_manager.remove_file_tag(file, tag["id"])
                    count += 1
                    progress.update(task, advance=1)
                return count

            # Run tag removal asynchronously
            count = asyncio.run(process_file_tags())

        # Show appropriate success message
        if all_tags:
            console.print(f"[bold green]✓[/] Removed all tags from {count} files")
        else:
            console.print(
                f"[bold green]✓[/] Removed tags {', '.join(f'[bold]{t}[/]' for t in tags)} from {count} files"
            )

    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error:[/] {str(e)}")


@tagging_app.command("list")
def list_tags(
    path: str | None = typer.Argument(None, help="Path to file or directory"),
    recursive: bool = typer.Option(
        False, "--recursive", "-r", help="Apply to all files in directory recursively"
    ),
    show_all: bool = typer.Option(
        False, "--all", "-a", help="List all tags in the system"
    ),
) -> None:
    """
    List tags for files or all tags in the system.

    Examples:
        aichemist tag list
        aichemist tag list path/to/file.py
        aichemist tag list path/to/dir -r
    """
    try:
        # Get tag manager
        tag_manager = get_tag_manager()

        # Initialize tag manager
        asyncio.run(tag_manager.initialize())

        # List all tags if requested
        if show_all:
            console.print("[bold]All tags in the system:[/]")
            tags = asyncio.run(tag_manager.get_all_tags())

            if not tags:
                console.print("[yellow]No tags found in the system.[/]")
                return

            # Create a table for tags
            table = Table(show_header=True, header_style="bold")
            table.add_column("Tag", style="cyan")

            # Add tags to table
            for tag in tags:
                table.add_row(tag["name"])

            console.print(table)
            return

        # List tags for specific files
        if path:
            target_path = Path(path).resolve()

            if not target_path.exists():
                raise FileNotFoundError(f"Path not found: {target_path}")

            files_to_check = []

            # Handle directory with recursive option
            if target_path.is_dir():
                if recursive:
                    console.print(
                        f"Scanning directory [bold]{target_path}[/] recursively..."
                    )
                    files_to_check.extend(
                        [
                            f
                            for f in target_path.rglob("*")
                            if f.is_file() and not f.name.startswith(".")
                        ]
                    )
                else:
                    console.print(f"Scanning directory [bold]{target_path}[/]...")
                    files_to_check.extend(
                        [
                            f
                            for f in target_path.glob("*")
                            if f.is_file() and not f.name.startswith(".")
                        ]
                    )
            else:
                # Single file
                files_to_check.append(target_path)

            # If no files found
            if not files_to_check:
                console.print("[yellow]No files found.[/]")
                return

            # Create a table for file tags
            table = Table(show_header=True, header_style="bold")
            table.add_column("File", style="cyan")
            table.add_column("Tags", style="green")

            async def get_file_tags():
                for file in files_to_check:
                    # Get tags for file
                    file_tags = await tag_manager.get_file_tags(file)

                    if file_tags:
                        tag_names = [tag.get("name", "") for tag in file_tags]
                        table.add_row(str(file), ", ".join(tag_names))
                    else:
                        table.add_row(str(file), "[dim italic]No tags[/]")

            # Run tag listing asynchronously
            asyncio.run(get_file_tags())

            console.print(table)
        else:
            # No path provided, show usage hint
            console.print(
                "[yellow]Please provide a path or use --all to list all tags.[/]"
            )

    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error:[/] {str(e)}")


@tagging_app.command("suggest")
def suggest_tags(
    path: str = typer.Argument(..., help="Path to file or directory"),
    recursive: bool = typer.Option(
        False, "--recursive", "-r", help="Apply to all files in directory recursively"
    ),
    threshold: float = typer.Option(
        0.7, "--threshold", "-t", help="Confidence threshold (0.0-1.0)"
    ),
    apply: bool = typer.Option(
        False, "--apply", "-a", help="Apply suggested tags automatically"
    ),
) -> None:
    """
    Suggest tags for files based on content analysis.

    Examples:
        aichemist tag suggest path/to/file.py
        aichemist tag suggest path/to/dir -r --threshold 0.6
        aichemist tag suggest path/to/file.py --apply
    """
    try:
        # Get tag manager and initialize
        tag_manager = get_tag_manager()
        asyncio.run(tag_manager.initialize())

        # Create file reader and tag suggester
        file_reader = FileReader()
        tag_suggester = TagSuggester(tag_manager)

        # Resolve the file or directory path
        target_path = Path(path).resolve()

        if not target_path.exists():
            raise FileNotFoundError(f"Path not found: {target_path}")

        files_to_process = []

        # Handle directory with recursive option
        if target_path.is_dir():
            if recursive:
                console.print(
                    f"Scanning directory [bold]{target_path}[/] recursively..."
                )
                files_to_process.extend(
                    [
                        f
                        for f in target_path.rglob("*")
                        if f.is_file() and not f.name.startswith(".")
                    ]
                )
            else:
                console.print(f"Scanning directory [bold]{target_path}[/]...")
                files_to_process.extend(
                    [
                        f
                        for f in target_path.glob("*")
                        if f.is_file() and not f.name.startswith(".")
                    ]
                )
        else:
            # Single file
            files_to_process.append(target_path)

        # If no files found
        if not files_to_process:
            console.print("[yellow]No files found to analyze.[/]")
            return

        # Process files with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Analyzing files and suggesting tags..."),
            transient=False,
        ) as progress:
            task = progress.add_task("suggest_tags", total=len(files_to_process))

            async def process_files():
                suggestions = {}

                for file in files_to_process:
                    # Get file metadata
                    metadata = FileMetadata.from_path(file)
                    if metadata.error:
                        console.print(
                            f"[yellow]Warning: Could not process {file}: {metadata.error}[/]"
                        )
                        progress.update(task, advance=1)
                        continue

                    # Process file to get more metadata
                    try:
                        metadata = await file_reader.process_file(file)
                    except Exception as e:
                        console.print(
                            f"[yellow]Warning: Error processing {file}: {str(e)}[/]"
                        )
                        progress.update(task, advance=1)
                        continue

                    # Get suggestions
                    file_suggestions = await tag_suggester.suggest_tags(
                        metadata, min_confidence=threshold
                    )

                    # Store suggestions
                    if file_suggestions:
                        suggestions[str(file)] = file_suggestions

                    # Apply tags if requested
                    if apply and file_suggestions:
                        await tag_manager.add_file_tags(file, file_suggestions)

                    progress.update(task, advance=1)

                return suggestions

            # Run tag suggestion asynchronously
            suggestions = asyncio.run(process_files())

        # Display results
        if not suggestions:
            console.print("[yellow]No tag suggestions were found.[/]")
            return

        console.print(f"\n[bold green]Tag suggestions for {len(suggestions)} files:[/]")

        # Create a table for suggestions
        table = Table(show_header=True, header_style="bold")
        table.add_column("File", style="cyan")
        table.add_column("Suggested Tags", style="green")
        table.add_column("Confidence", style="blue")

        # Add suggestions to table
        for file, file_suggestions in suggestions.items():
            tags_str = ", ".join([tag for tag, _ in file_suggestions])
            conf_str = ", ".join([f"{conf:.2f}" for _, conf in file_suggestions])
            table.add_row(file, tags_str, conf_str)

        console.print(table)

        # Show message about applied tags
        if apply:
            tag_count = sum(len(s) for s in suggestions.values())
            console.print(
                f"[bold green]✓[/] Applied {tag_count} suggested tags to {len(suggestions)} files"
            )

    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error:[/] {str(e)}")
