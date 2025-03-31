"""Command registration module for the AIchemist Codex CLI.

This module registers all CLI commands with the Typer application.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from the_aichemist_codex.interfaces.cli.cli_app import CLIApp


def register_commands(cli_app: "CLIApp") -> None:
    """Register all command modules with the CLI app.

    Args:
        cli_app: The CLI application instance
    """
    from the_aichemist_codex.interfaces.cli.commands import (
        analysis,
        artifacts,
        config,
        fs,
        init,
        memories,
        relationships,
        search,
        tagging,
        version,
    )

    # Register each command module with the CLI app
    init.register_commands(cli_app.app, cli_app)
    config.register_commands(cli_app.app, cli_app)
    fs.register_commands(cli_app.app, cli_app)
    artifacts.register_commands(cli_app.app, cli_app)
    memories.register_commands(cli_app.app, cli_app)
    analysis.register_commands(cli_app.app, cli_app)
    search.register_commands(cli_app.app, cli_app)
    version.register_commands(cli_app.app, cli_app)
    tagging.register_commands(cli_app.app, cli_app)
    relationships.register_commands(cli_app.app, cli_app)
