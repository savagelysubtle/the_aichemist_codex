"""Code analysis commands for the AIchemist Codex CLI."""

import asyncio
import json
from pathlib import Path
from typing import Any
from uuid import UUID

import typer
from rich.box import SIMPLE
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from the_aichemist_codex.domain.repositories.code_artifact_repository import (
    CodeArtifactRepository,
)
from the_aichemist_codex.domain.services.interfaces.code_analysis_service import (
    CodeAnalysisServiceInterface,
)
from the_aichemist_codex.infrastructure.analysis.code_analysis_service import (
    CodeAnalysisService,
)
from the_aichemist_codex.infrastructure.repositories.file_code_artifact_repository import (
    FileCodeArtifactRepository,
)

console = Console()
analysis_app = typer.Typer(help="Code analysis operations")

# Store reference to CLI instance
_cli: Any = None
# Repository instance - will be initialized in register_commands
_repository: CodeArtifactRepository | None = None
# Service instance - will be initialized in register_commands
_service: CodeAnalysisServiceInterface | None = None


def register_commands(app: typer.Typer, cli: Any) -> None:
    """Register analysis commands with the application."""
    global _cli, _repository, _service
    _cli = cli

    # Initialize repository with default storage location
    storage_dir = Path(
        cli.config.get(
            "artifacts.storage_dir", Path.home() / ".aichemist" / "artifacts"
        )
    )
    _repository = FileCodeArtifactRepository(storage_dir)

    # Initialize service
    _service = CodeAnalysisService(_repository)

    app.add_typer(analysis_app, name="analysis")


@analysis_app.command("analyze-file")
def analyze_file(
    file_path: str = typer.Argument(..., help="Path to the file to analyze"),
    depth: int = typer.Option(1, help="Analysis depth (1-3)"),
    output_format: str = typer.Option("table", help="Output format (table or json)"),
) -> None:
    """
    Analyze a file and display its code characteristics.

    Examples:
        aichemist analysis analyze-file src/main.py
        aichemist analysis analyze-file src/main.py --depth 2 --format json
    """
    try:
        # Validate depth
        if depth < 1 or depth > 3:
            raise ValueError("Depth must be between 1 and 3")

        path = Path(file_path)
        if not path.exists() or not path.is_file():
            console.print(
                f"[bold red]Error:[/] File {file_path} does not exist or is not a file"
            )
            return

        # Analyze the file
        if _service is None:
            raise RuntimeError("Analysis service not initialized")

        results = asyncio.run(_service.analyze_file(path, depth))
        if results is None:
            console.print(f"[yellow]No analysis results generated for {file_path}[/]")
            return

        _display_analysis_results(results, output_format)
    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error during analysis:[/] {e!s}")


@analysis_app.command("analyze-artifact")
def analyze_artifact(
    artifact_id: str = typer.Argument(..., help="ID of the artifact to analyze"),
    depth: int = typer.Option(1, help="Analysis depth (1-3)"),
    output_format: str = typer.Option("table", help="Output format (table or json)"),
) -> None:
    """
    Analyze a code artifact by its ID.

    Examples:
        aichemist analysis analyze-artifact 123e4567-e89b-12d3-a456-426614174000
        aichemist analysis analyze-artifact 123e4567-e89b-12d3-a456-426614174000 --depth 2
    """
    try:
        # Validate depth
        if depth < 1 or depth > 3:
            raise ValueError("Depth must be between 1 and 3")

        # Validate UUID format
        try:
            artifact_id_obj = UUID(artifact_id)
        except ValueError:
            console.print(f"[bold red]Error:[/] {artifact_id} is not a valid UUID")
            return

        # Analyze the artifact
        if _service is None:
            raise RuntimeError("Analysis service not initialized")

        if _repository is not None:
            artifact = _repository.get_by_id(artifact_id_obj)
            if not artifact:
                console.print(
                    f"[bold red]Error:[/] Artifact with ID {artifact_id} not found"
                )
                return

        results = asyncio.run(_service.analyze_artifact(artifact_id_obj, depth))
        if results is None:
            console.print(
                f"[yellow]No analysis results generated for artifact {artifact_id}[/]"
            )
            return

        _display_analysis_results(results, output_format)
    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error during analysis:[/] {e!s}")


@analysis_app.command("analyze-codebase")
def analyze_codebase(
    directory: str = typer.Argument(..., help="Path to the codebase directory"),
    pattern: str = typer.Option("*.py", help="File pattern to match (glob syntax)"),
    depth: int = typer.Option(1, help="Analysis depth (1-3)"),
    output_format: str = typer.Option("table", help="Output format (table or json)"),
) -> None:
    """
    Analyze a directory of code files.

    Examples:
        aichemist analysis analyze-codebase src/
        aichemist analysis analyze-codebase src/ --pattern "*.js" --depth 2
    """
    try:
        # Validate depth
        if depth < 1 or depth > 3:
            raise ValueError("Depth must be between 1 and 3")

        dir_path = Path(directory)
        if not dir_path.exists() or not dir_path.is_dir():
            console.print(
                f"[bold red]Error:[/] {directory} does not exist or is not a directory"
            )
            return

        # Analyze the codebase
        if _service is None:
            raise RuntimeError("Analysis service not initialized")

        results = asyncio.run(_service.analyze_codebase(dir_path, depth, pattern))
        if results is None:
            console.print(
                f"[yellow]No analysis results generated for codebase at {directory}[/]"
            )
            return

        _display_analysis_results(results, output_format)
    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error during analysis:[/] {e!s}")


@analysis_app.command("complexity")
def calculate_complexity(
    artifact_id: str = typer.Argument(..., help="ID of the artifact to analyze"),
) -> None:
    """
    Calculate the complexity score for a code artifact.

    Examples:
        aichemist analysis complexity 123e4567-e89b-12d3-a456-426614174000
    """
    try:
        # Validate UUID format
        try:
            artifact_id_obj = UUID(artifact_id)
        except ValueError:
            console.print(f"[bold red]Error:[/] {artifact_id} is not a valid UUID")
            return

        # Get the artifact first to display name
        if _repository is None:
            raise RuntimeError("Repository not initialized")

        artifact = _repository.get_by_id(artifact_id_obj)
        if not artifact:
            console.print(
                f"[bold red]Error:[/] Artifact with ID {artifact_id} not found"
            )
            return

        # Calculate complexity
        if _service is None:
            raise RuntimeError("Analysis service not initialized")

        complexity = asyncio.run(_service.calculate_complexity(artifact_id_obj))
        if complexity is None:
            console.print(
                f"[yellow]Could not calculate complexity for {artifact.name}[/]"
            )
            return

        # Display results
        table = Table(title=f"Complexity Analysis for {artifact.name}")
        table.add_column("Metric")
        table.add_column("Value")

        table.add_row("Complexity Score", f"{complexity:.2f}")

        # Assess complexity level
        assessment = "Low"
        if complexity > 15:
            assessment = "Very High"
        elif complexity > 10:
            assessment = "High"
        elif complexity > 5:
            assessment = "Medium"

        table.add_row("Assessment", assessment)

        console.print(Panel(table, box=SIMPLE))

    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error calculating complexity:[/] {e!s}")


@analysis_app.command("find-similar")
def find_similar_artifacts(
    artifact_id: str = typer.Argument(
        ..., help="ID of the artifact to find similar artifacts for"
    ),
    min_similarity: float = typer.Option(
        0.5, help="Minimum similarity score (0.0-1.0)"
    ),
    limit: int = typer.Option(5, help="Maximum number of results to display"),
) -> None:
    """
    Find artifacts similar to a given artifact.

    Examples:
        aichemist analysis find-similar 123e4567-e89b-12d3-a456-426614174000
        aichemist analysis find-similar 123e4567-e89b-12d3-a456-426614174000 --min-similarity 0.7
    """
    try:
        # Validate UUID format
        try:
            artifact_id_obj = UUID(artifact_id)
        except ValueError:
            console.print(f"[bold red]Error:[/] {artifact_id} is not a valid UUID")
            return

        # Get the artifact first to display name
        if _repository is None:
            raise RuntimeError("Repository not initialized")

        artifact = _repository.get_by_id(artifact_id_obj)
        if not artifact:
            console.print(
                f"[bold red]Error:[/] Artifact with ID {artifact_id} not found"
            )
            return

        # Find similar artifacts
        if _service is None:
            raise RuntimeError("Analysis service not initialized")

        similar_artifacts = asyncio.run(
            _service.find_similar_artifacts(artifact_id_obj, min_similarity, limit)
        )

        # Display results
        if not similar_artifacts:
            console.print(f"[yellow]No similar artifacts found for {artifact.name}[/]")
            return

        table = Table(title=f"Similar Artifacts to {artifact.name}")
        table.add_column("ID")
        table.add_column("Name")
        table.add_column("Path")
        table.add_column("Similarity", justify="right")

        for artifact_tuple in similar_artifacts:
            if artifact_tuple is None:
                continue

            similar_artifact, similarity = artifact_tuple
            if similar_artifact is None:
                continue

            table.add_row(
                str(similar_artifact.id)[:8] + "...",
                similar_artifact.name,
                str(similar_artifact.path),
                f"{similarity:.2f}",
            )

        console.print(Panel(table, box=SIMPLE))

    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error finding similar artifacts:[/] {e!s}")


@analysis_app.command("extract-knowledge")
def extract_knowledge(
    artifact_id: str = typer.Argument(
        ..., help="ID of the artifact to extract knowledge from"
    ),
    limit: int = typer.Option(5, help="Maximum number of knowledge items to display"),
) -> None:
    """
    Extract knowledge items from a code artifact.

    Examples:
        aichemist analysis extract-knowledge 123e4567-e89b-12d3-a456-426614174000
        aichemist analysis extract-knowledge 123e4567-e89b-12d3-a456-426614174000 --limit 10
    """
    try:
        # Validate UUID format
        try:
            artifact_id_obj = UUID(artifact_id)
        except ValueError:
            console.print(f"[bold red]Error:[/] {artifact_id} is not a valid UUID")
            return

        # Get the artifact first to display name
        if _repository is None:
            raise RuntimeError("Repository not initialized")

        artifact = _repository.get_by_id(artifact_id_obj)
        if not artifact:
            console.print(
                f"[bold red]Error:[/] Artifact with ID {artifact_id} not found"
            )
            return

        # Extract knowledge
        if _service is None:
            raise RuntimeError("Analysis service not initialized")

        knowledge_items = asyncio.run(
            _service.extract_knowledge(artifact_id_obj, limit)
        )

        # Display results
        if not knowledge_items:
            console.print(
                f"[yellow]No knowledge items extracted from {artifact.name}[/]"
            )
            return

        table = Table(title=f"Knowledge Items from {artifact.name}")
        table.add_column("Type")
        table.add_column("Content")
        table.add_column("Importance", justify="right")

        for item in knowledge_items:
            # Ensure item is not None before accessing
            if item is None:
                continue

            # Truncate content if it's too long
            content = item.get("content", "")
            if len(content) > 60:
                content = content[:57] + "..."

            table.add_row(
                item.get("type", "Unknown"), content, str(item.get("importance", 0))
            )

        console.print(Panel(table, box=SIMPLE))

    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error extracting knowledge:[/] {e!s}")


@analysis_app.command("find-dependencies")
def find_dependencies(
    artifact_id: str = typer.Argument(
        ..., help="ID of the artifact to find dependencies for"
    ),
    recursive: bool = typer.Option(
        False, help="Recursively find dependencies of dependencies"
    ),
) -> None:
    """
    Find dependencies of a code artifact.

    Examples:
        aichemist analysis find-dependencies 123e4567-e89b-12d3-a456-426614174000
        aichemist analysis find-dependencies 123e4567-e89b-12d3-a456-426614174000 --recursive
    """
    try:
        # Validate UUID format
        try:
            artifact_id_obj = UUID(artifact_id)
        except ValueError:
            console.print(f"[bold red]Error:[/] {artifact_id} is not a valid UUID")
            return

        # Get the artifact first to display name
        if _repository is None:
            raise RuntimeError("Repository not initialized")

        artifact = _repository.get_by_id(artifact_id_obj)
        if not artifact:
            console.print(
                f"[bold red]Error:[/] Artifact with ID {artifact_id} not found"
            )
            return

        # Find dependencies
        if _service is None:
            raise RuntimeError("Analysis service not initialized")

        dependencies = asyncio.run(
            _service.find_dependencies(artifact_id_obj, recursive)
        )

        # Display results
        if not dependencies:
            console.print(f"[yellow]No dependencies found for {artifact.name}[/]")
            return

        console.print(
            f"[bold]Found {len(dependencies)} dependencies for {artifact.name}[/]"
        )

        # Create dependency tree
        tree = Tree(f"[bold]{artifact.name}[/] ({str(artifact.id)[:8]}...)")

        for dep in dependencies:
            if dep is None:
                continue
            tree.add(f"[cyan]{dep.name}[/] ({str(dep.id)[:8]}...) - {dep.path}")

        console.print(tree)

    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error finding dependencies:[/] {e!s}")


@analysis_app.command("find-references")
def find_references(
    artifact_id: str = typer.Argument(
        ..., help="ID of the artifact to find references for"
    ),
    recursive: bool = typer.Option(
        False, help="Recursively find references to references"
    ),
) -> None:
    """
    Find references to a code artifact.

    Examples:
        aichemist analysis find-references 123e4567-e89b-12d3-a456-426614174000
        aichemist analysis find-references 123e4567-e89b-12d3-a456-426614174000 --recursive
    """
    try:
        # Validate UUID format
        try:
            artifact_id_obj = UUID(artifact_id)
        except ValueError:
            console.print(f"[bold red]Error:[/] {artifact_id} is not a valid UUID")
            return

        # Get the artifact first to display name
        if _repository is None:
            raise RuntimeError("Repository not initialized")

        artifact = _repository.get_by_id(artifact_id_obj)
        if not artifact:
            console.print(
                f"[bold red]Error:[/] Artifact with ID {artifact_id} not found"
            )
            return

        # Find references
        if _service is None:
            raise RuntimeError("Analysis service not initialized")

        references = asyncio.run(_service.find_references(artifact_id_obj, recursive))

        # Display results
        if not references:
            console.print(f"[yellow]No references found for {artifact.name}[/]")
            return

        console.print(f"[bold]Found {len(references)} references to {artifact.name}[/]")

        # Create reference tree
        tree = Tree(f"[bold]{artifact.name}[/] ({str(artifact.id)[:8]}...)")

        for ref in references:
            if ref is None:
                continue
            tree.add(f"[cyan]{ref.name}[/] ({str(ref.id)[:8]}...) - {ref.path}")

        console.print(tree)

    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error finding references:[/] {e!s}")


@analysis_app.command("get-summary")
def get_summary(
    artifact_id: str = typer.Argument(..., help="ID of the artifact to summarize"),
) -> None:
    """
    Get a summary of a code artifact.

    Examples:
        aichemist analysis get-summary 123e4567-e89b-12d3-a456-426614174000
    """
    try:
        # Validate UUID format
        try:
            artifact_id_obj = UUID(artifact_id)
        except ValueError:
            console.print(f"[bold red]Error:[/] {artifact_id} is not a valid UUID")
            return

        # Get the artifact first to display name
        if _repository is None:
            raise RuntimeError("Repository not initialized")

        artifact = _repository.get_by_id(artifact_id_obj)
        if not artifact:
            console.print(
                f"[bold red]Error:[/] Artifact with ID {artifact_id} not found"
            )
            return

        # Get summary
        if _service is None:
            raise RuntimeError("Analysis service not initialized")

        summary = asyncio.run(_service.get_summary(artifact_id_obj))
        if summary is None:
            console.print(f"[yellow]Could not generate summary for {artifact.name}[/]")
            return

        # Display results
        panel = Panel(
            summary,
            title=f"Summary of {artifact.name}",
            subtitle=f"ID: {str(artifact.id)[:8]}..., Path: {artifact.path}",
            box=SIMPLE,
        )
        console.print(panel)

    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error getting summary:[/] {e!s}")


@analysis_app.command("get-structure")
def get_structure(
    artifact_id: str = typer.Argument(
        ..., help="ID of the artifact to get structure for"
    ),
) -> None:
    """
    Get the structure of a code artifact.

    Examples:
        aichemist analysis get-structure 123e4567-e89b-12d3-a456-426614174000
    """
    try:
        # Validate UUID format
        try:
            artifact_id_obj = UUID(artifact_id)
        except ValueError:
            console.print(f"[bold red]Error:[/] {artifact_id} is not a valid UUID")
            return

        # Get the artifact first to display name
        if _repository is None:
            raise RuntimeError("Repository not initialized")

        artifact = _repository.get_by_id(artifact_id_obj)
        if not artifact:
            console.print(
                f"[bold red]Error:[/] Artifact with ID {artifact_id} not found"
            )
            return

        # Get structure
        if _service is None:
            raise RuntimeError("Analysis service not initialized")

        structure = asyncio.run(_service.get_structure(artifact_id_obj))
        if structure is None:
            console.print(f"[yellow]Could not get structure for {artifact.name}[/]")
            return

        # Display results
        console.print(
            f"[bold]Structure of {artifact.name}[/] ({str(artifact.id)[:8]}...)"
        )

        # Create structure tree
        tree = Tree(f"[bold]{artifact.name}[/]")

        if "classes" in structure:
            classes_branch = tree.add("[bold blue]Classes[/]")
            for class_info in structure["classes"]:
                if class_info is None:
                    continue

                class_branch = classes_branch.add(
                    f"[blue]{class_info.get('name', 'Unknown')}[/]"
                )

                # Add methods
                if "methods" in class_info:
                    for method in class_info["methods"]:
                        if method is None:
                            continue
                        class_branch.add(
                            f"[cyan]📋 {method.get('name', 'Unknown')}()[/]"
                        )

                # Add properties
                if "properties" in class_info:
                    for prop in class_info["properties"]:
                        if prop is None:
                            continue
                        class_branch.add(f"[green]🔹 {prop.get('name', 'Unknown')}[/]")

        if "functions" in structure:
            functions_branch = tree.add("[bold magenta]Functions[/]")
            for func in structure["functions"]:
                if func is None:
                    continue
                functions_branch.add(f"[magenta]📋 {func.get('name', 'Unknown')}()[/]")

        if "variables" in structure:
            vars_branch = tree.add("[bold green]Variables[/]")
            for var in structure["variables"]:
                if var is None:
                    continue
                vars_branch.add(f"[green]🔹 {var.get('name', 'Unknown')}[/]")

        console.print(tree)

    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error getting structure:[/] {e!s}")


def _display_analysis_results(
    results: dict[str, Any], output_format: str = "table"
) -> None:
    """Display analysis results in the specified format."""
    if results is None:
        console.print("[yellow]No results to display[/]")
        return

    if output_format == "json":
        console.print(json.dumps(results, indent=2, default=str))
    else:  # table format
        table = Table(title="Code Analysis Results", show_header=True)
        table.add_column("Property")
        table.add_column("Value")

        for key, value in results.items():
            if value is None:
                table.add_row(key, "N/A")
            elif isinstance(value, dict):
                # Create subtable for nested properties
                subtable = Table(show_header=False, box=None)
                subtable.add_column("")
                subtable.add_column("")

                for subkey, subvalue in value.items():
                    if subvalue is None:
                        subtable.add_row(subkey, "N/A")
                    else:
                        subtable.add_row(subkey, str(subvalue))

                table.add_row(key, subtable)
            elif isinstance(value, list):
                # Format list values
                if not value:
                    table.add_row(key, "[]")
                else:
                    formatted_items = []
                    for item in value:
                        if item is not None:
                            formatted_items.append(str(item))
                    formatted_value = "\n".join(formatted_items)
                    table.add_row(key, formatted_value or "[]")
            else:
                table.add_row(key, str(value))

        console.print(Panel(table, box=SIMPLE))
