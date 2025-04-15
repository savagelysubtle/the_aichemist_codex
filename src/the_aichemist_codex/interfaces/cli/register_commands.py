"""Command registration module for the AIchemist Codex CLI.

This module registers all CLI commands with the Typer application.
"""

import logging
from typing import TYPE_CHECKING

import typer  # Added import

if TYPE_CHECKING:
    from the_aichemist_codex.interfaces.cli.cli import CLI

logger = logging.getLogger(__name__)


def register_commands(
    typer_app: typer.Typer, cli_services: "CLI"
) -> None:  # Modified signature
    """Register all command modules with the CLI app.

    Args:
        typer_app: The Typer application instance.
        cli_services: The CLI service container instance.
    """
    # Defer imports until needed to avoid circular dependencies potentially
    try:
        from the_aichemist_codex.interfaces.cli.commands import (
            analysis,
            artifacts,
            config,
            fs,
            ingest,
            memory,
            relationships,
            search,
            tagging,
            version,
        )

        # Register each command module, passing both Typer app and CLI services
        # init.register_commands(typer_app, cli_services)
        # Remove or fix if init command exists

        config.register_commands(typer_app, cli_services)  # Updated call
        ingest.register_commands(typer_app, cli_services)  # Updated call
        fs.register_commands(typer_app, cli_services)  # Updated call
        artifacts.register_commands(typer_app, cli_services)  # Updated call
        analysis.register_commands(typer_app, cli_services)  # Updated call
        search.register_commands(typer_app, cli_services)  # Updated call
        version.register_commands(typer_app, cli_services)  # Updated call
        tagging.register_commands(typer_app, cli_services)  # Updated call
        relationships.register_commands(typer_app, cli_services)  # Updated call
        memory.register_commands(
            typer_app, cli_services
        )  # Added memory based on cli.py
    except ImportError as e:
        logger.error(f"Failed to import command module: {e}", exc_info=True)
        # Optionally re-raise or handle differently
        raise typer.Exit(code=1) from e
