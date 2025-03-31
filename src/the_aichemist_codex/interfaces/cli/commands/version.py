"""Version information commands for the AIchemist Codex CLI."""

import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel

console = Console()
version_app = typer.Typer(help="Version information")

# Store reference to CLI instance
_cli = None


def register_commands(app: Any, cli: Any) -> None:
    """Register version commands with the application."""
    global _cli
    _cli = cli
    app.add_typer(version_app, name="version")


@version_app.callback(invoke_without_command=True)
def version_callback(ctx: typer.Context):
    """
    Show version information.

    Examples:
        aichemist version
    """
    if ctx.invoked_subcommand is not None:
        return

    try:
        pkg_version = version("the_aichemist_codex")
    except PackageNotFoundError:
        pkg_version = "development"

    python_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )

    version_info = [
        f"AIchemist Codex: {pkg_version}",
        f"Python: {python_version}",
        f"Platform: {sys.platform}",
    ]

    console.print(
        Panel("\n".join(version_info), title="Version Information", expand=False)
    )
