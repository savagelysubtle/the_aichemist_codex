"""Main CLI module for the AIchemist Codex."""

import logging
from pathlib import Path

import typer
from rich.console import Console

from the_aichemist_codex.infrastructure.fs.directory import DirectoryManager
from the_aichemist_codex.infrastructure.fs.file_reader import FileReader

logger = logging.getLogger(__name__)
console = Console()


class CLI:
    """Main CLI class for the AIchemist Codex."""

    def __init__(
        self,
        base_dir: Path | None = None,
        directory_manager: DirectoryManager | None = None,
        file_reader: FileReader | None = None,
    ) -> None:
        """
        Initialize the CLI with required services.

        Args:
            base_dir: Optional base directory path override
            directory_manager: Optional DirectoryManager instance
            file_reader: Optional FileReader instance
        """
        # Initialize core services
        self.base_dir = base_dir
        self.directory_manager = directory_manager or DirectoryManager(base_dir)
        self.file_reader = file_reader or FileReader()
        self.console = Console()

    def handle_error(self, error: Exception) -> None:
        """Handle and format errors consistently."""
        if isinstance(error, FileNotFoundError):
            console.print(f"[bold red]Error:[/] File not found: {str(error)}")
        elif isinstance(error, PermissionError):
            console.print(f"[bold red]Error:[/] Permission denied: {str(error)}")
        elif isinstance(error, ValueError):
            console.print(f"[bold red]Error:[/] Invalid value: {str(error)}")
        else:
            console.print(f"[bold red]Error:[/] {str(error)}")
        logger.error(f"CLI error: {error}", exc_info=True)


# Create the Typer app
cli_app = typer.Typer(
    name="aichemist",
    help="AIchemist Codex - AI-powered code management and analysis tool",
    add_completion=True,
)

# Create CLI instance for use by command modules
_cli = CLI()


@cli_app.callback()
def callback() -> None:
    """AIchemist Codex CLI - Manage and analyze your codebase with AI assistance."""
    pass


# Import and register command groups after creating the app
from .commands import analysis, artifacts, config, fs, memory, search, version

# Register command groups
fs.register_commands(cli_app, _cli)
config.register_commands(cli_app, _cli)
version.register_commands(cli_app, _cli)
analysis.register_commands(cli_app, _cli)
artifacts.register_commands(cli_app, _cli)
memory.register_commands(cli_app, _cli)
search.register_commands(cli_app, _cli)

if __name__ == "__main__":
    cli_app()
