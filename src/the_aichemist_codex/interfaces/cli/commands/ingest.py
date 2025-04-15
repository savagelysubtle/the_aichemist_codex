# In a new interfaces/cli/commands/ingest.py or similar
import asyncio
from pathlib import Path
from typing import Any

import typer
from rich.console import Console

from the_aichemist_codex.infrastructure.utils.io.async_io import AsyncFileIO
from the_aichemist_codex.interfaces.ingest.aggregator import aggregate_digest
from the_aichemist_codex.interfaces.ingest.scanner import scan_directory

ingest_app = typer.Typer(help="Ingestion operations")
console = Console()
_cli = None  # Assume this gets set via register_commands


def register_commands(app: Any, cli: Any) -> None:
    global _cli
    _cli = cli
    app.add_typer(ingest_app, name="ingest")


@ingest_app.command("digest")
def create_digest(
    directory: str = typer.Argument(..., help="Directory to process"),
    output_file: str = typer.Option(None, "--output", "-o", help="Save digest to file"),
) -> None:
    """Generate a text digest of files in a directory."""

    async def _run_digest() -> None:
        try:
            dir_path = Path(directory).resolve()
            if not dir_path.is_dir():
                raise ValueError(f"Not a directory: {dir_path}")

            console.print(f"Scanning directory: {dir_path}...")
            # TODO: Get include/ignore patterns from config
            file_paths = scan_directory(dir_path)

            if not file_paths:
                console.print("[yellow]No files found to include in digest.[/]")
                return

            console.print(f"Reading {len(file_paths)} files...")
            content_map = {}
            tasks = [AsyncFileIO.read_text(fp) for fp in file_paths]
            contents = await asyncio.gather(*tasks)

            for fp, content in zip(file_paths, contents, strict=False):
                if not content.startswith("# Error"):  # Check for read errors
                    content_map[fp] = content
                else:
                    console.print(f"[yellow]Skipping file due to read error: {fp}[/]")

            console.print("Aggregating digest...")
            digest = aggregate_digest(file_paths, content_map)

            if output_file:
                out_path = Path(output_file)
                await AsyncFileIO.write(out_path, digest)
                console.print(f"[green]Digest saved to: {out_path}[/green]")
            else:
                console.print("\n--- Project Digest ---")
                console.print(digest)
                console.print("--- End Digest ---")

        except Exception as e:
            if _cli:
                _cli.handle_error(e)
            else:
                console.print(f"[bold red]Error: {e}[/bold red]")

    asyncio.run(_run_digest())
