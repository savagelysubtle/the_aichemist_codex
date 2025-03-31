# CLI Architecture Structure

## Entry Points

### 1. CLI Entry Point (src/the_aichemist_codex/cli.py)

```python
#!/usr/bin/env python
"""Command-line interface entry point."""

from the_aichemist_codex.interfaces.cli.cli import cli_app

if __name__ == "__main__":
    cli_app()
```

Purpose:

- Provides the main entry point for CLI execution
- Ensures proper Python path setup
- Imports and runs the CLI application

### 2. Main CLI Implementation (src/the_aichemist_codex/interfaces/cli/cli.py)

```python
class CLI:
    """Main CLI class for service management."""
    def __init__(
        self,
        base_dir: Path | None = None,
        directory_manager: DirectoryManager | None = None,
        file_reader: FileReader | None = None,
    ) -> None:
        # Service initialization
        pass

# Create Typer app instance
cli_app = typer.Typer(
    name="aichemist",
    help="AIchemist Codex - AI-powered code management and analysis tool",
    add_completion=True,
)

# Register command groups
fs.register_commands(cli_app, _cli)
config.register_commands(cli_app, _cli)
# ...etc
```

Purpose:

- Manages core CLI services
- Handles command registration
- Provides error handling
- Initializes the Typer application

## Directory Structure

```
src/the_aichemist_codex/
├── cli.py                 # CLI entry point
└── interfaces/
    └── cli/
        ├── __init__.py
        ├── cli.py        # Main CLI implementation
        ├── commands/     # Command implementations
        └── formatters/   # Output formatters
```

## Implementation Strategy

### 1. Entry Point Enhancement

The CLI entry point (cli.py) should:

- Remain minimal and focused
- Handle environment setup
- Provide clear error messages for import issues
- Support future CLI variants (e.g., debug mode)

```python
#!/usr/bin/env python
"""Enhanced CLI entry point."""

import sys
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from the_aichemist_codex.interfaces.cli.cli import cli_app
except ImportError as e:
    logger.error(f"Failed to import CLI application: {e}")
    sys.exit(1)

def main():
    """CLI entry point with error handling."""
    try:
        cli_app()
    except Exception as e:
        logger.error(f"CLI execution failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### 2. Main CLI Enhancement

The main CLI implementation (interfaces/cli/cli.py) should:

- Use dependency injection for services
- Provide centralized error handling
- Support command registration
- Manage CLI state

```python
class CLI:
    """Enhanced CLI implementation."""

    def __init__(
        self,
        base_dir: Path | None = None,
        services: dict[str, Any] | None = None,
    ) -> None:
        """Initialize CLI with service injection."""
        self.base_dir = base_dir
        self._services = services or {}
        self._initialize_services()

    def _initialize_services(self) -> None:
        """Initialize required services."""
        if "directory_manager" not in self._services:
            self._services["directory_manager"] = DirectoryManager(self.base_dir)
        if "file_reader" not in self._services:
            self._services["file_reader"] = FileReader()

    def get_service(self, service_name: str) -> Any:
        """Get service by name."""
        if service_name not in self._services:
            raise ValueError(f"Service not found: {service_name}")
        return self._services[service_name]
```

### 3. Command Registration

Command registration should:

- Support dependency injection
- Provide type safety
- Enable command discovery
- Support command grouping

```python
def register_commands(app: typer.Typer, cli: CLI) -> None:
    """Enhanced command registration."""
    # Register command groups with proper typing
    for command_module in COMMAND_MODULES:
        command_module.register_commands(app, cli)
```

## Service Management

### 1. Service Registry

```python
class ServiceRegistry:
    """Central service management."""

    def __init__(self):
        self._services: dict[str, Any] = {}

    def register(self, name: str, service: Any) -> None:
        """Register a service."""
        self._services[name] = service

    def get(self, name: str) -> Any:
        """Get a service by name."""
        return self._services[name]
```

### 2. Service Configuration

```python
class ServiceConfig:
    """Service configuration management."""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self._config = self._load_config()

    def get_service_config(self, service_name: str) -> dict:
        """Get configuration for a service."""
        return self._config.get(service_name, {})
```

## Error Handling

### 1. Error Hierarchy

```python
class CLIError(Exception):
    """Base CLI error."""
    pass

class ServiceError(CLIError):
    """Service-related error."""
    pass

class CommandError(CLIError):
    """Command execution error."""
    pass
```

### 2. Error Handler

```python
class ErrorHandler:
    """Centralized error handling."""

    def __init__(self, console: Console):
        self.console = console

    def handle(self, error: Exception) -> None:
        """Handle different types of errors."""
        if isinstance(error, CLIError):
            self._handle_cli_error(error)
        else:
            self._handle_unknown_error(error)
```

## Implementation Notes

1. **Service Initialization**
   - Use lazy loading for services
   - Support service configuration
   - Enable service mocking for tests

2. **Command Registration**
   - Support dynamic command discovery
   - Enable command dependencies
   - Provide command metadata

3. **Error Handling**
   - Centralize error handling
   - Support error recovery
   - Provide detailed error context

4. **Testing Support**
   - Enable service mocking
   - Support command testing
   - Provide test utilities
