"""Artifact commands for the AIchemist Codex CLI."""

import json
import os
from pathlib import Path
from typing import Any
from uuid import UUID

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from the_aichemist_codex.domain.entities.code_artifact import CodeArtifact
from the_aichemist_codex.domain.exceptions.repository_exception import RepositoryError
from the_aichemist_codex.domain.exceptions.validation_exception import (
    ValidationException,
)
from the_aichemist_codex.infrastructure.repositories.file_code_artifact_repository import (
    FileCodeArtifactRepository,
)

console = Console()
artifacts_app = typer.Typer(help="Code artifact operations")

# Store reference to CLI instance
_cli = None
# Repository instance
_repository = None


def register_commands(app: typer.Typer, cli: Any) -> None:
    """Register artifact commands with the application."""
    global _cli, _repository
    _cli = cli

    # Initialize repository with default storage location
    storage_dir = Path(
        os.environ.get("AICHEMIST_STORAGE", Path.home() / ".aichemist" / "artifacts")
    )
    _repository = FileCodeArtifactRepository(storage_dir)

    app.add_typer(artifacts_app, name="artifacts")


@artifacts_app.command("list")
def list_artifacts(
    name: str = typer.Option(None, "--name", "-n", help="Filter by artifact name"),
    type: str = typer.Option(None, "--type", "-t", help="Filter by artifact type"),
    format: str = typer.Option(
        "table", "--format", "-f", help="Output format (table, json)"
    ),
):
    """
    List code artifacts in the repository.

    Examples:
        aichemist artifacts list
        aichemist artifacts list --name main.py
        aichemist artifacts list --type file --format json
    """
    try:
        # Get all artifacts and apply filters
        artifacts = []

        if _repository is None:
            console.print("[bold red]Error:[/] Repository not initialized")
            return

        if name:
            artifacts = _repository.get_by_name(name)
        else:
            artifacts = _repository.find_all()

        # Apply type filter if specified
        if type and artifacts:
            artifacts = [a for a in artifacts if a.artifact_type == type]

        # Display results based on format
        if format.lower() == "json":
            result = []
            for artifact in artifacts:
                result.append(
                    {
                        "id": str(artifact.id),
                        "name": artifact.name,
                        "path": str(artifact.path),
                        "type": artifact.artifact_type,
                        "metadata": artifact.metadata,
                    }
                )
            console.print(
                Syntax(
                    json.dumps(result, indent=2),
                    "json",
                    theme="monokai",
                    line_numbers=True,
                )
            )
        else:  # Default to table
            table = Table(show_header=True, header_style="bold")
            table.add_column("ID", style="dim")
            table.add_column("Name")
            table.add_column("Type")
            table.add_column("Path")
            table.add_column("Content Size", justify="right")

            for artifact in artifacts:
                content_size = len(artifact.content or "") if artifact.content else 0
                table.add_row(
                    str(artifact.id)[:8] + "...",  # Truncated ID for readability
                    artifact.name,
                    artifact.artifact_type,
                    str(artifact.path),
                    f"{content_size} chars",
                )

            console.print(table)
            console.print(f"[dim]Total: {len(artifacts)} artifact(s)[/]")

    except RepositoryError as e:
        if _cli:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Repository Error:[/] {e!s}")


@artifacts_app.command("show")
def show_artifact(
    id: str = typer.Argument(..., help="ID of the artifact to show"),
    show_content: bool = typer.Option(
        True, "--content/--no-content", help="Show artifact content"
    ),
):
    """
    Show details of a specific code artifact.

    Examples:
        aichemist artifacts show 123e4567-e89b-12d3-a456-426614174000
        aichemist artifacts show 123e4567-e89b-12d3-a456-426614174000 --no-content
    """
    try:
        # Parse the UUID
        artifact_id = UUID(id)

        # Check if repository is initialized
        if _repository is None:
            console.print("[bold red]Error:[/] Repository not initialized")
            return

        # Get the artifact
        artifact = _repository.get_by_id(artifact_id)

        if not artifact:
            console.print(f"[bold red]Error:[/] Artifact with ID {id} not found")
            return

        # Display artifact details
        console.print(Panel(f"[bold]Code Artifact: {artifact.name}[/]", expand=False))

        # Details table
        table = Table(show_header=False, box=None)
        table.add_column("Property", style="cyan")
        table.add_column("Value")

        table.add_row("ID", str(artifact.id))
        table.add_row("Name", artifact.name)
        table.add_row("Type", artifact.artifact_type)
        table.add_row("Path", str(artifact.path))
        table.add_row("Valid", "✓" if artifact.is_valid else "✗")

        if artifact.metadata:
            metadata_str = json.dumps(artifact.metadata, indent=2)
            table.add_row("Metadata", metadata_str)

        console.print(table)

        # Show content if requested and available
        if show_content and artifact.content:
            console.print("\n[bold]Content:[/]")
            # Try to detect language for syntax highlighting
            file_ext = artifact.path.suffix.lower() if artifact.path.suffix else ""
            language = None

            if file_ext in [".py", ".pyw"]:
                language = "python"
            elif file_ext in [".js", ".jsx"]:
                language = "javascript"
            elif file_ext in [".ts", ".tsx"]:
                language = "typescript"
            elif file_ext in [".html", ".htm"]:
                language = "html"
            elif file_ext in [".css"]:
                language = "css"
            elif file_ext in [".json"]:
                language = "json"
            elif file_ext in [".md", ".markdown"]:
                language = "markdown"

            console.print(
                Syntax(
                    artifact.content,
                    language or "text",
                    theme="monokai",
                    line_numbers=True,
                    word_wrap=True,
                )
            )

    except ValueError:
        console.print(f"[bold red]Error:[/] Invalid UUID format: {id}")
    except RepositoryError as e:
        if _cli:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Repository Error:[/] {e!s}")


@artifacts_app.command("create")
def create_artifact(
    path: str = typer.Argument(..., help="Path to the file to create an artifact from"),
    name: str = typer.Option(
        None, "--name", "-n", help="Name for the artifact (defaults to filename)"
    ),
    type: str = typer.Option("file", "--type", "-t", help="Type of the artifact"),
):
    """
    Create a new code artifact from a file.

    Examples:
        aichemist artifacts create src/main.py
        aichemist artifacts create src/main.py --name "Main Module" --type module
    """
    try:
        file_path = Path(path).resolve()

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"Not a file: {file_path}")

        # Read file content
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Create artifact
        artifact = CodeArtifact(
            path=file_path,
            name=name or file_path.name,
            artifact_type=type,
            content=content,
        )

        # Check if repository is initialized
        if _repository is None:
            console.print("[bold red]Error:[/] Repository not initialized")
            return

        # Save to repository
        saved_artifact = _repository.save(artifact)

        console.print(f"[green]Successfully created artifact:[/] {saved_artifact.name}")
        console.print(f"[dim]ID: {saved_artifact.id}[/]")

    except ValidationException as e:
        console.print(f"[bold red]Validation Error:[/] {e.message}")
        for field, msg in e.errors.items():
            console.print(f"  - {field}: {msg}")
    except (FileNotFoundError, ValueError, RepositoryError) as e:
        if _cli:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error:[/] {e!s}")


@artifacts_app.command("delete")
def delete_artifact(
    id: str = typer.Argument(..., help="ID of the artifact to delete"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force deletion without confirmation"
    ),
):
    """
    Delete a code artifact from the repository.

    Examples:
        aichemist artifacts delete 123e4567-e89b-12d3-a456-426614174000
        aichemist artifacts delete 123e4567-e89b-12d3-a456-426614174000 --force
    """
    try:
        # Parse the UUID
        artifact_id = UUID(id)

        # Check if repository is initialized
        if _repository is None:
            console.print("[bold red]Error:[/] Repository not initialized")
            return

        # Get the artifact for display
        artifact = _repository.get_by_id(artifact_id)

        if not artifact:
            console.print(f"[bold red]Error:[/] Artifact with ID {id} not found")
            return

        # Confirm deletion unless forced
        if not force:
            console.print("You are about to delete the following artifact:")
            console.print(f"  [bold]{artifact.name}[/] (ID: {artifact.id})")
            console.print(f"  Path: {artifact.path}")
            console.print(f"  Type: {artifact.artifact_type}")

            confirm = typer.confirm("Are you sure you want to delete this artifact?")
            if not confirm:
                console.print("[yellow]Deletion cancelled.[/]")
                return

        # Delete the artifact
        success = _repository.delete(artifact_id)

        if success:
            console.print(f"[green]Successfully deleted artifact:[/] {artifact.name}")
        else:
            console.print("[yellow]Artifact not found or already deleted.[/]")

    except ValueError:
        console.print(f"[bold red]Error:[/] Invalid UUID format: {id}")
    except RepositoryError as e:
        if _cli:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Repository Error:[/] {e!s}")


@artifacts_app.command("snippet")
def get_snippet(
    id: str = typer.Argument(..., help="ID of the artifact"),
    start: int = typer.Option(..., "--start", "-s", help="Start line (1-indexed)"),
    end: int = typer.Option(..., "--end", "-e", help="End line (1-indexed)"),
):
    """
    Get a specific code snippet from an artifact.

    Examples:
        aichemist artifacts snippet 123e4567-e89b-12d3-a456-426614174000 --start 10 --end 20
    """
    try:
        # Parse the UUID
        artifact_id = UUID(id)

        # Check if repository is initialized
        if _repository is None:
            console.print("[bold red]Error:[/] Repository not initialized")
            return

        # Get the artifact
        artifact = _repository.get_by_id(artifact_id)

        if not artifact:
            console.print(f"[bold red]Error:[/] Artifact with ID {id} not found")
            return

        # Get the snippet
        snippet = artifact.get_snippet(start, end)

        # Display the snippet with syntax highlighting
        file_ext = artifact.path.suffix.lower() if artifact.path.suffix else ""
        language = None

        if file_ext in [".py", ".pyw"]:
            language = "python"
        elif file_ext in [".js", ".jsx"]:
            language = "javascript"
        elif file_ext in [".ts", ".tsx"]:
            language = "typescript"
        elif file_ext in [".html", ".htm"]:
            language = "html"
        elif file_ext in [".css"]:
            language = "css"
        elif file_ext in [".json"]:
            language = "json"
        elif file_ext in [".md", ".markdown"]:
            language = "markdown"

        console.print(f"[bold]Snippet from {artifact.name} (lines {start}-{end}):[/]")
        console.print(
            Syntax(
                snippet,
                language or "text",
                theme="monokai",
                line_numbers=True,
                start_line=start,
                word_wrap=True,
            )
        )

    except ValueError as e:
        console.print(f"[bold red]Error:[/] {e!s}")
    except RepositoryError as e:
        if _cli:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Repository Error:[/] {e!s}")
