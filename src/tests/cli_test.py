#!/usr/bin/env python
"""
Simple test script for the AIchemist Codex CLI.
This avoids dependencies on other components that might not be fully implemented yet.
"""

from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(help="AIchemist Codex CLI Test")
console = Console()


@app.command("list")
def list_directory(
    path: str = typer.Argument(".", help="Directory path to list"),
    details: bool = typer.Option(
        False, "--details", "-d", help="Show detailed information"
    ),
):
    """List contents of a directory."""
    console.print(f"[bold]Listing directory:[/] {path}")
    dir_path = Path(path)

    if not dir_path.exists():
        console.print(f"[red]Error:[/] Directory not found: {path}")
        return

    if not dir_path.is_dir():
        console.print(f"[red]Error:[/] Not a directory: {path}")
        return

    items = list(dir_path.iterdir())

    console.print(f"Found {len(items)} items:")
    for item in items:
        if item.is_dir():
            console.print(f"[blue]{item.name}/[/]")
        else:
            console.print(f"{item.name}")


@app.command("info")
def show_info():
    """Show information about the AIchemist Codex."""
    console.print("[bold]AIchemist Codex[/]")
    console.print("A tool for AI-powered code management and analysis")
    console.print("Version: 0.1.0 (Development)")


if __name__ == "__main__":
    app()
