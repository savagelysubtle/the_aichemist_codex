"""Code analysis commands for the AIchemist Codex CLI."""

import asyncio
import json
from pathlib import Path
from typing import Any
from uuid import UUID

import typer
from rich.box import SIMPLE
from rich.console import Console
from rich.table import Table

from the_aichemist_codex.application.dto.analysis_result_dto import AnalysisResultDTO
from the_aichemist_codex.application.services.code_analysis_service import (
    ApplicationCodeAnalysisService,
)
from the_aichemist_codex.domain.repositories.code_artifact_repository import (
    CodeArtifactRepository,
)
from the_aichemist_codex.infrastructure.analysis.technical_analyzer import (
    TechnicalCodeAnalyzer,
)
from the_aichemist_codex.infrastructure.repositories.file_code_artifact_repository import (
    FileCodeArtifactRepository,
)
from the_aichemist_codex.interfaces.cli.cli import CLI

console = Console()
analysis_app = typer.Typer(help="Code analysis operations")

# Store reference to CLI instance
_cli: Any = None
# Repository instance - will be initialized in register_commands
_repository: CodeArtifactRepository | None = None
# Service instance - will be initialized in register_commands
_service: ApplicationCodeAnalysisService | None = None


def register_commands(app: typer.Typer, cli_services: CLI) -> None:
    """Register analysis commands with the application."""
    global _cli, _repository, _service
    _cli = cli_services

    # Initialize repository with default storage location
    storage_dir = Path.home() / ".aichemist" / "artifacts"
    _repository = FileCodeArtifactRepository(storage_dir)

    # Initialize technical analyzer
    technical_analyzer = TechnicalCodeAnalyzer(_repository)

    # Initialize application service
    _service = ApplicationCodeAnalysisService(_repository, technical_analyzer)

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

        results = asyncio.run(_service.analyze_file(str(path), depth))
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
    include_structure: bool = typer.Option(
        False, "--structure", "-s", help="Include code structure analysis"
    ),
    max_knowledge: int = typer.Option(
        10, "--max-knowledge", "-k", help="Maximum knowledge items to extract"
    ),
) -> None:
    """
    Analyze a code artifact by its ID.

    Examples:
        aichemist analysis analyze-artifact 123e4567-e89b-12d3-a456-426614174000
        aichemist analysis analyze-artifact 123e4567-e89b-12d3-a456-426614174000 \
            --structure
    """
    try:
        # Validate UUID format
        try:
            artifact_id_obj = UUID(artifact_id)
        except ValueError:
            console.print(f"[bold red]Error:[/] {artifact_id} is not a valid UUID")
            return

        # Analyze the artifact
        if _service is None:
            raise RuntimeError("Analysis service not initialized")

        results = asyncio.run(
            _service.get_artifact_analysis(
                artifact_id=artifact_id_obj,
                include_structure=include_structure,
                max_knowledge_items=max_knowledge,
            )
        )

        if results is None:
            console.print(
                f"[yellow]No analysis results generated for artifact {artifact_id}[/]"
            )
            return

        _display_analysis_results(results)
    except ValueError as e:
        console.print(f"[bold red]Error:[/] {e!s}")
    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error during analysis:[/] {e!s}")


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
    Find artifacts similar to the given one.

    Examples:
        aichemist analysis find-similar 123e4567-e89b-12d3-a456-426614174000
        aichemist analysis find-similar 123e4567-e89b-12d3-a456-426614174000 \
            --min-similarity 0.7
    """
    try:
        # Validate UUID format
        try:
            artifact_id_obj = UUID(artifact_id)
        except ValueError:
            console.print(f"[bold red]Error:[/] {artifact_id} is not a valid UUID")
            return

        # Find similar artifacts
        if _service is None:
            raise RuntimeError("Analysis service not initialized")

        similar_artifacts = asyncio.run(
            _service.find_similar_artifacts(artifact_id_obj, min_similarity, limit)
        )

        if not similar_artifacts:
            console.print(f"[yellow]No similar artifacts found for {artifact_id}[/]")
            return

        # Display results
        table = Table(title="Similar Artifacts", box=SIMPLE)
        table.add_column("ID")
        table.add_column("Similarity")
        table.add_column("Summary")

        for artifact in similar_artifacts:
            table.add_row(
                str(artifact.artifact_id),
                f"{artifact.complexity:.2f}",  # Using complexity as similarity score
                artifact.summary or "No summary available",
            )

        console.print(table)
    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error finding similar artifacts:[/] {e!s}")


def _display_analysis_results(
    results: AnalysisResultDTO, output_format: str = "table"
) -> None:
    """Display analysis results in the specified format."""
    if output_format == "json":
        # Convert to dictionary and print as JSON
        result_dict = {
            "artifact_id": str(results.artifact_id),
            "complexity": results.complexity,
            "summary": results.summary,
            "knowledge_items": results.knowledge_items,
            "structure": results.structure,
        }
        console.print(json.dumps(result_dict, indent=2))
        return

    # Display as table/tree format
    console.print()
    console.print(
        f"[bold green]Analysis Results for Artifact:[/] {results.artifact_id}"
    )
    console.print()

    # Complexity
    if results.complexity is not None:
        console.print(f"[bold]Complexity Score:[/] {results.complexity:.2f}")
        console.print()

    # Summary
    if results.summary:
        console.print("[bold]Summary:[/]")
        console.print(results.summary)
        console.print()

    # Knowledge Items
    if results.knowledge_items and len(results.knowledge_items) > 0:
        console.print("[bold]Knowledge Extracted:[/]")
        for item in results.knowledge_items:
            console.print(f"- {item.get('item', 'Unknown item')}")
        console.print()

    # Structure (conditionally included)
    if results.structure:
        console.print("[bold]Code Structure:[/]")
        for section, elements in results.structure.items():
            console.print(f"[bold]{section}:[/]")
            for element in elements:
                console.print(
                    f"  - {element.get('name', 'Unnamed')}: "
                    f"{element.get('type', 'Unknown type')}"
                )
        console.print()
