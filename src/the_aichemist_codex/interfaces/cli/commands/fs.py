"""File system commands for the AIchemist Codex CLI."""

import os
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table

console = Console()
fs_app = typer.Typer(help="File system operations")

# Store reference to CLI instance
_cli = None


def register_commands(app: Any, cli: Any) -> None:
    """Register file system commands with the application."""
    global _cli
    _cli = cli
    app.add_typer(fs_app, name="fs")


@fs_app.command("list")
def list_directory(
    path: str = typer.Argument(".", help="Directory path to list"),
    details: bool = typer.Option(
        False, "--details", "-d", help="Show detailed information"
    ),
    hidden: bool = typer.Option(False, "--hidden", "-a", help="Show hidden files"),
    recursive: bool = typer.Option(
        False, "--recursive", "-r", help="List directories recursively"
    ),
    depth: int = typer.Option(1, "--depth", help="Maximum depth for recursive listing"),
) -> None:
    """
    List contents of a directory.

    Examples:
        aichemist fs list
        aichemist fs list ./src --details
        aichemist fs list ./config --hidden
    """
    try:
        # Convert to Path and resolve
        dir_path = Path(path).resolve()

        # Ensure directory exists
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")

        if not dir_path.is_dir():
            raise ValueError(f"Not a directory: {dir_path}")

        # Get directory contents
        items = []

        if recursive and depth > 0:
            # Recursive listing with depth control
            for current_depth, (current_dir, dirs, files) in enumerate(
                os.walk(dir_path)
            ):
                if current_depth >= depth:
                    # Remove subdirectories to prevent deeper traversal
                    dirs.clear()
                    continue

                rel_path = Path(current_dir).relative_to(dir_path)
                if rel_path != Path("."):  # Not the root directory
                    items.append((rel_path, True, Path(current_dir)))

                for file in files:
                    if not hidden and file.startswith("."):
                        continue
                    file_path = Path(current_dir) / file
                    rel_file_path = file_path.relative_to(dir_path)
                    items.append((rel_file_path, False, file_path))
        else:
            # Simple non-recursive listing
            for item in dir_path.iterdir():
                # Skip hidden files unless requested
                if not hidden and item.name.startswith("."):
                    continue

                items.append((Path(item.name), item.is_dir(), item))

        # Sort: directories first, then files, alphabetically
        items.sort(key=lambda x: (not x[1], str(x[0]).lower()))

        if details:
            # Create a rich table for detailed view
            table = Table(show_header=True, header_style="bold")
            table.add_column("Type")
            table.add_column("Name")
            table.add_column("Size", justify="right")
            table.add_column("Modified")

            for name, is_dir, item_path in items:
                try:
                    item_stat = item_path.stat()
                    size = "-" if is_dir else f"{item_stat.st_size:,}"
                    modified = _format_timestamp(item_stat.st_mtime)
                    item_type = "DIR" if is_dir else "FILE"
                    table.add_row(
                        f"[blue]{item_type}[/]" if is_dir else f"[green]{item_type}[/]",
                        str(name),
                        size,
                        modified,
                    )
                except Exception as e:
                    # Handle any errors accessing file information
                    table.add_row("[red]ERR[/]", str(name), "-", f"Error: {e!s}")

            console.print(f"Contents of [bold cyan]{escape(str(dir_path))}[/]:")
            console.print(table)
        else:
            # Simple list view
            console.print(f"Contents of [bold cyan]{escape(str(dir_path))}[/]:")

            for name, is_dir, _ in items:
                if is_dir:
                    console.print(f"[blue]{name}/[/]")
                else:
                    console.print(f"{name}")

    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error:[/] {e!s}")


@fs_app.command("read")
def read_file(
    path: str = typer.Argument(..., help="File path to read"),
    lines: int | None = typer.Option(
        None, "--lines", "-n", help="Number of lines to read"
    ),
    head: int | None = typer.Option(None, "--head", "-h", help="Read first N lines"),
    tail: int | None = typer.Option(None, "--tail", "-t", help="Read last N lines"),
) -> None:
    """
    Read and display file contents.

    Examples:
        aichemist fs read filename.txt
        aichemist fs read config.json --head 10
        aichemist fs read logs.txt --tail 20
    """
    try:
        file_path = Path(path).resolve()

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"Not a file: {file_path}")

        # Get MIME type to determine if it's binary
        if _cli is not None and hasattr(_cli, "file_reader"):
            mime_type = _cli.file_reader.get_mime_type(file_path)
        else:
            mime_type = "unknown/unknown"

        if "text/" not in mime_type and "application/json" not in mime_type:
            console.print(
                f"[yellow]Warning:[/] File appears to be binary ({mime_type})"
            )

        # Read the file
        with open(file_path, encoding="utf-8", errors="replace") as f:
            if head:
                content = "".join([next(f) for _ in range(head)])
            elif tail:
                content = "".join(get_tail_lines(file_path, tail))
            elif lines:
                content = "".join([next(f) for _ in range(lines)])
            else:
                content = f.read()

        # Display the content
        console.print(f"[bold cyan]{escape(str(file_path))}[/]:")
        console.print(content)

    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error:[/] {e!s}")


@fs_app.command("info")
def file_info(
    path: str = typer.Argument(..., help="File or directory path"),
) -> None:
    """
    Display detailed information about a file or directory.

    Examples:
        aichemist fs info filename.txt
        aichemist fs info ./src
    """
    try:
        item_path = Path(path).resolve()

        if not item_path.exists():
            raise FileNotFoundError(f"Path not found: {item_path}")

        # Get basic stats
        stats = item_path.stat()

        console.print(f"[bold cyan]Information for: {escape(str(item_path))}[/]")
        console.print(f"Type: {'Directory' if item_path.is_dir() else 'File'}")
        console.print(f"Size: {stats.st_size:,} bytes")
        console.print(f"Created: {_format_timestamp(stats.st_ctime)}")
        console.print(f"Modified: {_format_timestamp(stats.st_mtime)}")
        console.print(f"Accessed: {_format_timestamp(stats.st_atime)}")

        if item_path.is_file():
            # Get MIME type for files
            if _cli is not None and hasattr(_cli, "file_reader"):
                mime_type = _cli.file_reader.get_mime_type(item_path)
            else:
                mime_type = "unknown/unknown"
            console.print(f"MIME Type: {mime_type}")

    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error:[/] {e!s}")


# Helper functions
def _format_timestamp(timestamp: float) -> str:
    """Format a timestamp into a human-readable string."""
    from datetime import datetime

    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_tail_lines(file_path: Path, num_lines: int) -> list[str]:
    """Get the last N lines from a file."""
    with open(file_path, encoding="utf-8", errors="replace") as f:
        return list(f)[-num_lines:]
