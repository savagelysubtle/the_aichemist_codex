"""Configuration commands for the AIchemist Codex CLI."""

import json
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

console = Console()
config_app = typer.Typer(help="Configuration operations")

# Store reference to CLI instance
_cli = None

# Default config locations
DEFAULT_CONFIG_DIR = Path.home() / ".aichemist"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"


def register_commands(app: Any, cli: Any) -> None:
    """Register configuration commands with the application."""
    global _cli
    _cli = cli
    app.add_typer(config_app, name="config")


@config_app.command("list")
def list_config(
    output_format: str = typer.Option(
        "table", "--format", "-f", help="Output format (table, json)"
    ),
    section: str | None = typer.Option(
        None, "--section", "-s", help="Configuration section to show"
    ),
) -> None:
    """
    List all configuration settings.

    Examples:
        aichemist config list
        aichemist config list --format json
        aichemist config list --section paths
    """
    try:
        config = _load_config()

        if not config:
            console.print(
                "[yellow]No configuration found or configuration is empty.[/]"
            )
            return

        if section:
            if section in config:
                config = {section: config[section]}
            else:
                console.print(
                    f"[yellow]Section '{section}' not found in configuration.[/]"
                )
                return

        if output_format.lower() == "json":
            # Display as formatted JSON
            json_str = json.dumps(config, indent=2)
            syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
            console.print(syntax)
        else:
            # Display as table
            table = Table(show_header=True, header_style="bold")
            table.add_column("Section")
            table.add_column("Key")
            table.add_column("Value")

            for section_name, section_data in config.items():
                if isinstance(section_data, dict):
                    for key, value in section_data.items():
                        table.add_row(section_name, key, _format_value(value))
                else:
                    table.add_row("", section_name, _format_value(section_data))

            console.print(table)

    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error:[/] {str(e)}")


@config_app.command("get")
def get_config(
    key: str = typer.Argument(
        ..., help="Configuration key to retrieve (can be section.key)"
    ),
    default: str | None = typer.Option(
        None, "--default", "-d", help="Default value if key doesn't exist"
    ),
) -> None:
    """
    Get a specific configuration value.

    Examples:
        aichemist config get paths.data_dir
        aichemist config get logging.level --default INFO
    """
    try:
        config = _load_config()

        # Handle dot notation for nested keys (section.key)
        parts = key.split(".")

        if len(parts) > 1:
            section = parts[0]
            key_name = parts[1]

            if section in config and isinstance(config[section], dict):
                if key_name in config[section]:
                    value = config[section][key_name]
                    console.print(_format_value(value))
                else:
                    if default is not None:
                        console.print(default)
                    else:
                        console.print(
                            f"[yellow]Key '{key_name}' not found in section '{section}'.[/]"
                        )
            else:
                if default is not None:
                    console.print(default)
                else:
                    console.print(
                        f"[yellow]Section '{section}' not found in configuration.[/]"
                    )
        else:
            if key in config:
                value = config[key]
                console.print(_format_value(value))
            else:
                if default is not None:
                    console.print(default)
                else:
                    console.print(f"[yellow]Key '{key}' not found in configuration.[/]")

    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error:[/] {str(e)}")


@config_app.command("set")
def set_config(
    key: str = typer.Argument(
        ..., help="Configuration key to set (can be section.key)"
    ),
    value: str = typer.Argument(..., help="Value to set"),
    value_type: str = typer.Option(
        "auto", "--type", "-t", help="Value type (auto, str, int, float, bool, json)"
    ),
) -> None:
    """
    Set a configuration value.

    Examples:
        aichemist config set paths.data_dir /path/to/data
        aichemist config set logging.level DEBUG
        aichemist config set cache.enabled true --type bool
        aichemist config set project.tags '["python", "ai"]' --type json
    """
    try:
        config = _load_config()

        # Convert value based on type
        parsed_value = _parse_value(value, value_type)

        # Handle dot notation for nested keys (section.key)
        parts = key.split(".")

        if len(parts) > 1:
            section = parts[0]
            key_name = parts[1]

            # Create section if it doesn't exist
            if section not in config:
                config[section] = {}
            elif not isinstance(config[section], dict):
                console.print(
                    f"[yellow]Warning: Converting '{section}' from {config[section].__class__.__name__} to dictionary.[/]"
                )
                config[section] = {}

            # Set the value in the section
            config[section][key_name] = parsed_value
            console.print(
                f"Set [green]{section}.{key_name}[/] to [blue]{_format_value(parsed_value)}[/]"
            )
        else:
            # Set top-level value
            config[key] = parsed_value
            console.print(
                f"Set [green]{key}[/] to [blue]{_format_value(parsed_value)}[/]"
            )

        # Save the configuration
        _save_config(config)

    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error:[/] {str(e)}")


@config_app.command("init")
def init_config(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force initialization even if config already exists",
    ),
    template: str | None = typer.Option(
        None, "--template", "-t", help="Template file to use for initialization"
    ),
) -> None:
    """
    Initialize a new configuration file with default settings.

    Examples:
        aichemist config init
        aichemist config init --force
        aichemist config init --template /path/to/template.json
    """
    try:
        config_path = DEFAULT_CONFIG_FILE

        # Check if config already exists
        if config_path.exists() and not force:
            console.print(
                f"[yellow]Configuration file already exists at {config_path}[/]"
            )
            console.print("Use --force to overwrite existing configuration.")
            return

        # Create config directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize with template or default config
        if template:
            template_path = Path(template)
            if not template_path.exists():
                raise FileNotFoundError(f"Template file not found: {template_path}")

            with open(template_path) as f:
                config = json.load(f)
        else:
            # Default configuration
            config = {
                "paths": {
                    "data_dir": str(Path.home() / ".aichemist" / "data"),
                    "cache_dir": str(Path.home() / ".aichemist" / "cache"),
                    "log_dir": str(Path.home() / ".aichemist" / "logs"),
                },
                "logging": {
                    "level": "INFO",
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "file_enabled": True,
                    "console_enabled": True,
                },
                "ai": {
                    "provider": "openai",
                    "model": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 1000,
                },
                "ui": {"theme": "dark", "color_scheme": "default", "verbose": True},
                "system": {
                    "max_threads": 4,
                    "auto_update": True,
                    "telemetry_enabled": False,
                },
                "storage": {
                    "format": "json",
                    "compression": False,
                    "backup_enabled": True,
                    "max_backups": 5,
                },
            }

        # Save the configuration
        _save_config(config, config_path)

        console.print(
            f"[green]Configuration initialized successfully at {config_path}[/]"
        )
        console.print("Use 'aichemist config list' to view the configuration.")

    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error:[/] {str(e)}")


@config_app.command("import")
def import_config(
    file: str = typer.Argument(..., help="JSON file to import configuration from"),
    merge: bool = typer.Option(
        True,
        "--merge/--replace",
        help="Merge with existing config or replace completely",
    ),
) -> None:
    """
    Import configuration from a JSON file.

    Examples:
        aichemist config import config.json
        aichemist config import config.json --replace
    """
    try:
        import_path = Path(file)
        if not import_path.exists():
            raise FileNotFoundError(f"Import file not found: {import_path}")

        # Load import file
        with open(import_path) as f:
            import_config = json.load(f)

        if merge:
            # Merge with existing config
            config = _load_config()
            _deep_update(config, import_config)
            console.print("[green]Merged configuration from import file.[/]")
        else:
            # Replace config completely
            config = import_config
            console.print("[green]Replaced configuration with import file.[/]")

        # Save the configuration
        _save_config(config)

        console.print(
            f"[green]Configuration imported successfully from {import_path}[/]"
        )

    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error:[/] {str(e)}")


@config_app.command("export")
def export_config(
    file: str = typer.Argument(..., help="JSON file to export configuration to"),
    section: str | None = typer.Option(
        None, "--section", "-s", help="Export only this section"
    ),
    pretty: bool = typer.Option(
        True, "--pretty/--compact", help="Pretty format JSON with indentation"
    ),
) -> None:
    """
    Export configuration to a JSON file.

    Examples:
        aichemist config export my_config.json
        aichemist config export paths.json --section paths
        aichemist config export config.json --compact
    """
    try:
        export_path = Path(file)

        # Load current config
        config = _load_config()

        # Export only a specific section if requested
        if section:
            if section in config:
                config = {section: config[section]}
            else:
                console.print(
                    f"[yellow]Section '{section}' not found in configuration.[/]"
                )
                return

        # Create directory if it doesn't exist
        export_path.parent.mkdir(parents=True, exist_ok=True)

        # Save to export file
        with open(export_path, "w") as f:
            indent = 2 if pretty else None
            json.dump(config, f, indent=indent)

        console.print(f"[green]Configuration exported successfully to {export_path}[/]")

    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error:[/] {str(e)}")


@config_app.command("reset")
def reset_config(
    section: str | None = typer.Option(
        None, "--section", "-s", help="Reset only this section"
    ),
    confirm: bool = typer.Option(
        True, "--confirm/--no-confirm", help="Confirm before resetting"
    ),
) -> None:
    """
    Reset configuration to defaults.

    Examples:
        aichemist config reset
        aichemist config reset --section logging
        aichemist config reset --no-confirm
    """
    try:
        if confirm:
            reset_type = f"section '{section}'" if section else "all configuration"
            should_proceed = typer.confirm(
                f"Are you sure you want to reset {reset_type}?"
            )
            if not should_proceed:
                console.print("[yellow]Reset cancelled.[/]")
                return

        # Initialize with default config
        if section:
            # Reset only the specified section
            config = _load_config()

            # Initialize with default config
            default_config = {
                "paths": {
                    "data_dir": str(Path.home() / ".aichemist" / "data"),
                    "cache_dir": str(Path.home() / ".aichemist" / "cache"),
                    "log_dir": str(Path.home() / ".aichemist" / "logs"),
                },
                "logging": {
                    "level": "INFO",
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "file_enabled": True,
                    "console_enabled": True,
                },
                "ai": {
                    "provider": "openai",
                    "model": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 1000,
                },
                "ui": {"theme": "dark", "color_scheme": "default", "verbose": True},
                "system": {
                    "max_threads": 4,
                    "auto_update": True,
                    "telemetry_enabled": False,
                },
                "storage": {
                    "format": "json",
                    "compression": False,
                    "backup_enabled": True,
                    "max_backups": 5,
                },
            }

            if section in default_config:
                config[section] = default_config[section]
                console.print(f"[green]Reset section '{section}' to defaults.[/]")
            else:
                console.print(
                    f"[yellow]No default configuration found for section '{section}'.[/]"
                )
                return
        else:
            # Reset all configuration
            init_config(force=True)
            return

        # Save the configuration
        _save_config(config)

    except Exception as e:
        if _cli is not None:
            _cli.handle_error(e)
        else:
            console.print(f"[bold red]Error:[/] {str(e)}")


# Helper functions
def _load_config() -> dict[str, Any]:
    """Load configuration from the default location."""
    config_path = DEFAULT_CONFIG_FILE

    if not config_path.exists():
        return {}

    try:
        with open(config_path) as f:
            return json.load(f)
    except json.JSONDecodeError:
        console.print(
            f"[yellow]Warning: Configuration file {config_path} is not valid JSON. Using empty configuration.[/]"
        )
        return {}
    except Exception as e:
        console.print(
            f"[yellow]Warning: Failed to load configuration: {str(e)}. Using empty configuration.[/]"
        )
        return {}


def _save_config(config: dict[str, Any], config_path: Path | None = None) -> None:
    """Save configuration to the specified or default location."""
    if config_path is None:
        config_path = DEFAULT_CONFIG_FILE

    # Create directory if it doesn't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)


def _parse_value(value: str, type_hint: str) -> Any:
    """Parse a string value into the specified type."""
    if type_hint == "auto":
        # Try to infer the type
        if value.lower() in ("true", "false"):
            return value.lower() == "true"
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            # If it's not a number or boolean, treat as string
            return value
    elif type_hint == "str":
        return value
    elif type_hint == "int":
        return int(value)
    elif type_hint == "float":
        return float(value)
    elif type_hint == "bool":
        if value.lower() in ("true", "yes", "1", "on"):
            return True
        elif value.lower() in ("false", "no", "0", "off"):
            return False
        raise ValueError(f"Cannot convert '{value}' to boolean")
    elif type_hint == "json":
        return json.loads(value)
    else:
        raise ValueError(f"Unknown type: {type_hint}")


def _format_value(value: Any) -> str:
    """Format a value for display."""
    if isinstance(value, dict):
        return json.dumps(value)
    elif isinstance(value, list | tuple):
        return json.dumps(value)
    elif isinstance(value, bool):
        return str(value).lower()
    else:
        return str(value)


def _deep_update(target: dict, source: dict) -> None:
    """Recursively update a dictionary."""
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            _deep_update(target[key], value)
        else:
            target[key] = value
