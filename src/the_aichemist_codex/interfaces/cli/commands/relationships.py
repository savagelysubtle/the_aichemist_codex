"""Relationship commands for the AIchemist Codex CLI.

This module provides commands for working with file relationships, including creating,
listing, and removing relationships between files.
"""

import asyncio
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from the_aichemist_codex.domain.relationships import RelationshipManager
from the_aichemist_codex.infrastructure.fs.file_reader import FileReader

console = Console()
relationships_app = typer.Typer(help="Manage relationships between files")

# Store reference to CLI instance
_cli = None
# Store reference to relationship manager
_relationship_manager = None
# Default database path
_db_path = Path.home() / ".aichemist" / "relationships.db"


def register_commands(app: Any, cli: Any) -> None:
    """Register relationship commands with the application."""
    global _cli, _relationship_manager, _db_path
    _cli = cli

    # Set database path based on CLI config if available
    if hasattr(cli, "config") and cli.config:
        config_db_path = getattr(cli.config, "relationships_db_path", None)
        if config_db_path:
            _db_path = Path(config_db_path)

    # Ensure the database directory exists
    _db_path.parent.mkdir(parents=True, exist_ok=True)

    app.add_typer(relationships_app, name="rel")


def get_relationship_manager() -> RelationshipManager:
    """Get or create relationship manager instance."""
    global _relationship_manager, _db_path
    if _relationship_manager is None:
        _relationship_manager = RelationshipManager(_db_path)
    return _relationship_manager


@relationships_app.command("create")
def create_relationship(
    source: str = typer.Argument(..., help="Path to source file"),
    target: str = typer.Argument(..., help="Path to target file"),
    type: str = typer.Argument(
        ..., help="Type of relationship (e.g., imports, extends, uses)"
    ),
    strength: float = typer.Option(
        1.0, "--strength", "-s", help="Relationship strength (0.0-1.0)"
    ),
    bidirectional: bool = typer.Option(
        False, "--bidirectional", "-b", help="Create relationship in both directions"
    ),
    metadata: list[str] = typer.Option(
        [], "--metadata", "-m", help="Additional metadata in key=value format"
    ),
) -> None:
    """
    Create a relationship between two files.

    Examples:
        aichemist rel create src/module.py src/utils.py imports
        aichemist rel create src/component.tsx src/api.ts uses --strength 0.8
        aichemist rel create src/class.py src/base.py extends --bidirectional
        aichemist rel create src/config.py src/app.py uses --metadata author=john reason=configuration
    """
    try:
        # Get relationship manager
        rel_manager = get_relationship_manager()

        # Initialize relationship manager
        asyncio.run(rel_manager.initialize())

        # Resolve the file paths
        source_path = Path(source).resolve()
        target_path = Path(target).resolve()

        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        if not target_path.exists():
            raise FileNotFoundError(f"Target file not found: {target_path}")

        # Parse metadata
        metadata_dict = {}
        for item in metadata:
            if "=" in item:
                key, value = item.split("=", 1)
                metadata_dict[key.strip()] = value.strip()

        # Create relationship with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Creating relationship..."),
            transient=True,
        ) as progress:
            task = progress.add_task(
                "create_relationship", total=1 if not bidirectional else 2
            )

            # Create relationship
            asyncio.run(
                rel_manager.create_relationship(
                    source_path,
                    target_path,
                    rel_type=type,
                    strength=strength,
                    metadata=metadata_dict,
                )
            )
            progress.update(task, advance=1)

            # Create reverse relationship if bidirectional
            if bidirectional:
                asyncio.run(
                    rel_manager.create_relationship(
                        target_path,
                        source_path,
                        rel_type=type,
                        strength=strength,
                        metadata=metadata_dict,
                    )
                )
                progress.update(task, advance=1)

        # Success message
        if bidirectional:
            console.print(
                f"[bold green]✓[/] Created bidirectional [bold]{type}[/] relationship between:"
            )
            console.print(f"  - [cyan]{source_path}[/]")
            console.print(f"  - [cyan]{target_path}[/]")
        else:
            console.print(f"[bold green]✓[/] Created [bold]{type}[/] relationship:")
            console.print(f"  - [cyan]{source_path}[/] → [cyan]{target_path}[/]")

    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error:[/] {e!s}")


@relationships_app.command("list")
def list_relationships(
    path: str | None = typer.Argument(None, help="Path to file"),
    outgoing: bool = typer.Option(
        True, "--outgoing/--no-outgoing", help="Show outgoing relationships"
    ),
    incoming: bool = typer.Option(
        True, "--incoming/--no-incoming", help="Show incoming relationships"
    ),
    type: str | None = typer.Option(
        None, "--type", "-t", help="Filter by relationship type"
    ),
    show_all: bool = typer.Option(
        False, "--all", "-a", help="List all relationships in the system"
    ),
) -> None:
    """
    List relationships for a file or all relationships in the system.

    Examples:
        aichemist rel list src/module.py
        aichemist rel list src/component.tsx --no-incoming
        aichemist rel list src/class.py --type extends
        aichemist rel list --all
    """
    try:
        # Get relationship manager
        rel_manager = get_relationship_manager()

        # Initialize relationship manager
        asyncio.run(rel_manager.initialize())

        # List all relationships if requested
        if show_all:
            console.print("[bold]All relationships in the system:[/]")
            relationships = asyncio.run(rel_manager.get_all_relationships())

            if not relationships:
                console.print("[yellow]No relationships found in the system.[/]")
                return

            # Create a table for relationships
            table = Table(show_header=True, header_style="bold")
            table.add_column("Source", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Target", style="cyan")
            table.add_column("Strength", style="blue")

            # Add relationships to table
            for rel in relationships:
                table.add_row(
                    str(rel.get("source_path", "")),
                    rel.get("type", ""),
                    str(rel.get("target_path", "")),
                    f"{rel.get('strength', 1.0):.2f}",
                )

            console.print(table)
            return

        # List relationships for specific file
        if path:
            target_path = Path(path).resolve()

            if not target_path.exists():
                raise FileNotFoundError(f"Path not found: {target_path}")

            # Get relationships
            outgoing_rels = []
            incoming_rels = []

            if outgoing:
                outgoing_rels = asyncio.run(
                    rel_manager.get_outgoing_relationships(target_path)
                )

            if incoming:
                incoming_rels = asyncio.run(
                    rel_manager.get_incoming_relationships(target_path)
                )

            # Filter by type if specified
            if type:
                outgoing_rels = [r for r in outgoing_rels if r.get("type") == type]
                incoming_rels = [r for r in incoming_rels if r.get("type") == type]

            # If no relationships found
            if not outgoing_rels and not incoming_rels:
                console.print(f"[yellow]No relationships found for {target_path}.[/]")
                return

            # Display relationships
            console.print(f"[bold]Relationships for [cyan]{target_path}[/]:[/]")

            if outgoing:
                console.print("\n[bold]Outgoing Relationships:[/]")
                if outgoing_rels:
                    table = Table(show_header=True, header_style="bold")
                    table.add_column("Type", style="green")
                    table.add_column("Target", style="cyan")
                    table.add_column("Strength", style="blue")

                    for rel in outgoing_rels:
                        table.add_row(
                            rel.get("type", ""),
                            str(rel.get("target_path", "")),
                            f"{rel.get('strength', 1.0):.2f}",
                        )

                    console.print(table)
                else:
                    console.print("[dim italic]No outgoing relationships.[/]")

            if incoming:
                console.print("\n[bold]Incoming Relationships:[/]")
                if incoming_rels:
                    table = Table(show_header=True, header_style="bold")
                    table.add_column("Source", style="cyan")
                    table.add_column("Type", style="green")
                    table.add_column("Strength", style="blue")

                    for rel in incoming_rels:
                        table.add_row(
                            str(rel.get("source_path", "")),
                            rel.get("type", ""),
                            f"{rel.get('strength', 1.0):.2f}",
                        )

                    console.print(table)
                else:
                    console.print("[dim italic]No incoming relationships.[/]")
        else:
            # No path provided, show usage hint
            console.print(
                "[yellow]Please provide a path or use --all to list all relationships.[/]"
            )

    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error:[/] {e!s}")


@relationships_app.command("remove")
def remove_relationship(
    source: str = typer.Argument(..., help="Path to source file"),
    target: str = typer.Argument(..., help="Path to target file"),
    type: str | None = typer.Option(
        None,
        "--type",
        "-t",
        help="Type of relationship to remove (remove all types if not specified)",
    ),
    bidirectional: bool = typer.Option(
        False, "--bidirectional", "-b", help="Remove relationship in both directions"
    ),
) -> None:
    """
    Remove a relationship between files.

    Examples:
        aichemist rel remove src/module.py src/utils.py
        aichemist rel remove src/component.tsx src/api.ts --type uses
        aichemist rel remove src/class.py src/base.py --bidirectional
    """
    try:
        # Get relationship manager
        rel_manager = get_relationship_manager()

        # Initialize relationship manager
        asyncio.run(rel_manager.initialize())

        # Resolve the file paths
        source_path = Path(source).resolve()
        target_path = Path(target).resolve()

        # Create relationship with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Removing relationship..."),
            transient=True,
        ) as progress:
            task = progress.add_task(
                "remove_relationship", total=1 if not bidirectional else 2
            )

            # Remove relationship
            removed = asyncio.run(
                rel_manager.remove_relationship(source_path, target_path, rel_type=type)
            )
            progress.update(task, advance=1)

            # Remove reverse relationship if bidirectional
            bidirectional_removed = 0
            if bidirectional:
                bidirectional_removed = asyncio.run(
                    rel_manager.remove_relationship(
                        target_path, source_path, rel_type=type
                    )
                )
                progress.update(task, advance=1)

        # Success message based on results
        if removed + bidirectional_removed == 0:
            console.print("[yellow]No matching relationships found to remove.[/]")
        elif bidirectional:
            console.print(
                f"[bold green]✓[/] Removed {removed + bidirectional_removed} relationships between:"
            )
            console.print(f"  - [cyan]{source_path}[/]")
            console.print(f"  - [cyan]{target_path}[/]")
        else:
            console.print(f"[bold green]✓[/] Removed {removed} relationships from:")
            console.print(f"  - [cyan]{source_path}[/] → [cyan]{target_path}[/]")

    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error:[/] {e!s}")


@relationships_app.command("detect")
def detect_relationships(
    path: str = typer.Argument(..., help="Path to file or directory"),
    recursive: bool = typer.Option(
        False, "--recursive", "-r", help="Process directory recursively"
    ),
    types: list[str] = typer.Option(
        ["imports", "includes", "references"],
        "--types",
        "-t",
        help="Relationship types to detect",
    ),
    apply: bool = typer.Option(
        False, "--apply", "-a", help="Apply detected relationships"
    ),
) -> None:
    """
    Automatically detect relationships between files.

    Examples:
        aichemist rel detect src/module.py
        aichemist rel detect src/components --recursive
        aichemist rel detect src/utils.py --types imports references --apply
    """
    try:
        # Get relationship manager
        rel_manager = get_relationship_manager()

        # Initialize relationship manager
        asyncio.run(rel_manager.initialize())

        # Resolve the file path
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
            console.print("[yellow]No files found to process.[/]")
            return

        # Process files with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Detecting relationships..."),
            transient=False,
        ) as progress:
            task = progress.add_task(
                "detect_relationships", total=len(files_to_process)
            )

            # Create file reader
            file_reader = FileReader()

            # Store detected relationships
            all_relationships = []

            for file in files_to_process:
                detected = []

                try:
                    # Detect relationships
                    detected = asyncio.run(
                        rel_manager.detect_relationships(file, relationship_types=types)
                    )

                    # Apply relationships if requested
                    if apply and detected:
                        for rel in detected:
                            asyncio.run(
                                rel_manager.create_relationship(
                                    rel["source_path"],
                                    rel["target_path"],
                                    rel_type=rel["type"],
                                    strength=rel.get("strength", 1.0),
                                    metadata=rel.get("metadata", {}),
                                )
                            )

                    all_relationships.extend(detected)

                except Exception as e:
                    console.print(f"[yellow]Warning: Error processing {file}: {e!s}[/]")

                progress.update(task, advance=1)

        # Display results
        if not all_relationships:
            console.print("[yellow]No relationships detected.[/]")
            return

        console.print(
            f"\n[bold green]Detected {len(all_relationships)} relationships:[/]"
        )

        # Group by relationship type
        relationships_by_type = {}
        for rel in all_relationships:
            rel_type = rel.get("type", "unknown")
            if rel_type not in relationships_by_type:
                relationships_by_type[rel_type] = []
            relationships_by_type[rel_type].append(rel)

        # Display by type
        for rel_type, rels in relationships_by_type.items():
            console.print(f"\n[bold]Type: {rel_type}[/] ({len(rels)} relationships)")

            table = Table(show_header=True, header_style="bold")
            table.add_column("Source", style="cyan")
            table.add_column("Target", style="cyan")
            table.add_column("Strength", style="blue")

            for rel in rels[:10]:  # Show only first 10 of each type
                table.add_row(
                    str(rel.get("source_path", "")),
                    str(rel.get("target_path", "")),
                    f"{rel.get('strength', 1.0):.2f}",
                )

            console.print(table)

            if len(rels) > 10:
                console.print(f"[dim italic]...and {len(rels) - 10} more[/]")

        # Show message about applied relationships
        if apply:
            console.print(
                f"[bold green]✓[/] Applied {len(all_relationships)} detected relationships"
            )
        else:
            console.print(
                "\n[dim]Use --apply to create these relationships in the database[/]"
            )

    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error:[/] {e!s}")


@relationships_app.command("visualize")
def visualize_relationships(
    path: str = typer.Argument(..., help="Path to file or directory"),
    recursive: bool = typer.Option(
        False, "--recursive", "-r", help="Include files in directory recursively"
    ),
    depth: int = typer.Option(
        1, "--depth", "-d", help="Relationship depth to visualize"
    ),
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (if not provided, display in console)",
    ),
    format: str = typer.Option(
        "tree", "--format", "-f", help="Output format: tree, dot, or json"
    ),
) -> None:
    """
    Visualize relationships between files.

    Examples:
        aichemist rel visualize src/module.py
        aichemist rel visualize src/components --recursive --depth 2
        aichemist rel visualize src/app.py --output graph.dot --format dot
    """
    try:
        # Get relationship manager
        rel_manager = get_relationship_manager()

        # Initialize relationship manager
        asyncio.run(rel_manager.initialize())

        # Resolve the file path
        target_path = Path(path).resolve()

        if not target_path.exists():
            raise FileNotFoundError(f"Path not found: {target_path}")

        files_to_visualize = []

        # Handle directory with recursive option
        if target_path.is_dir():
            if recursive:
                console.print(
                    f"Scanning directory [bold]{target_path}[/] recursively..."
                )
                files_to_visualize.extend(
                    [
                        f
                        for f in target_path.rglob("*")
                        if f.is_file() and not f.name.startswith(".")
                    ]
                )
            else:
                console.print(f"Scanning directory [bold]{target_path}[/]...")
                files_to_visualize.extend(
                    [
                        f
                        for f in target_path.glob("*")
                        if f.is_file() and not f.name.startswith(".")
                    ]
                )
        else:
            # Single file
            files_to_visualize.append(target_path)

        # If no files found
        if not files_to_visualize:
            console.print("[yellow]No files found to visualize.[/]")
            return

        # Visualize relationships
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Generating visualization..."),
            transient=True,
        ) as progress:
            task = progress.add_task("visualize", total=1)

            # Get visualization
            visualization = asyncio.run(
                rel_manager.visualize_relationships(
                    files_to_visualize, depth=depth, format=format
                )
            )

            progress.update(task, advance=1)

        # Output visualization
        if format == "tree" and not output:
            # Display tree in console
            console.print("\n[bold]Relationship Tree:[/]")
            console.print(visualization)
        elif output:
            # Write to file
            output_path = Path(output)
            output_path.write_text(visualization)
            console.print(
                f"[bold green]✓[/] Visualization saved to: [cyan]{output_path}[/]"
            )
        else:
            # Display in console
            console.print("\n[bold]Relationship Visualization:[/]")
            console.print(visualization)

    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error:[/] {e!s}")
