# CLI Command Implementation Patterns

## Command Module Structure

### 1. Module Organization

```python
"""Command module docstring describing purpose."""

# Imports
from typing import Any
import typer
from rich.console import Console

# Service and repository imports
from domain.services import ServiceInterface
from infrastructure.repositories import Repository

# Create command group
command_group = typer.Typer(help="Command group description")

# Service/repository references
_service: ServiceInterface | None = None
_repository: Repository | None = None
```

### 2. Command Registration

```python
def register_commands(app: typer.Typer, cli: Any) -> None:
    """Register commands with the application.

    Args:
        app: The Typer application instance
        cli: The CLI instance for service access
    """
    global _service, _repository

    # Initialize services and repositories
    _repository = get_repository(cli.config)
    _service = get_service(_repository)

    # Register command group
    app.add_typer(command_group, name="group-name")
```

## Command Implementation Patterns

### 1. Command Structure

```python
@command_group.command()
def command_name(
    required_param: str = typer.Argument(..., help="Parameter description"),
    optional_param: str = typer.Option(None, help="Optional parameter description"),
) -> None:
    """Command description and usage examples.

    Examples:
        command_name required-value
        command_name required-value --optional-param value
    """
    try:
        # 1. Parameter validation
        validate_parameters(required_param, optional_param)

        # 2. Service initialization check
        ensure_services()

        # 3. Command execution
        result = execute_command(required_param, optional_param)

        # 4. Result display
        display_result(result)

    except Exception as e:
        handle_error(e)
```

### 2. Validation Patterns

```python
def validate_parameters(*args, **kwargs) -> None:
    """Validate command parameters."""
    # Type validation
    if not isinstance(param, expected_type):
        raise ValueError(f"Invalid parameter type: {param}")

    # Value validation
    if param < min_value or param > max_value:
        raise ValueError(f"Parameter must be between {min_value} and {max_value}")

    # Format validation
    if not matches_format(param):
        raise ValueError(f"Invalid format: {param}")
```

### 3. Service Management

```python
def ensure_services() -> None:
    """Ensure required services are initialized."""
    if _service is None:
        raise RuntimeError("Service not initialized")
    if _repository is None:
        raise RuntimeError("Repository not initialized")
```

### 4. Result Display

```python
def display_result(result: Any) -> None:
    """Display command results."""
    if isinstance(result, dict):
        display_dict_result(result)
    elif isinstance(result, list):
        display_list_result(result)
    else:
        display_simple_result(result)
```

## Error Handling Patterns

### 1. Error Categories

```python
def handle_error(error: Exception) -> None:
    """Handle command errors."""
    if isinstance(error, ValidationError):
        handle_validation_error(error)
    elif isinstance(error, ServiceError):
        handle_service_error(error)
    elif isinstance(error, RepositoryError):
        handle_repository_error(error)
    else:
        handle_unknown_error(error)
```

### 2. Error Display

```python
def display_error(error: str, context: str | None = None) -> None:
    """Display formatted error message."""
    message = f"[bold red]Error:[/] {error}"
    if context:
        message += f"\nContext: {context}"
    console.print(message)
```

## Output Formatting Patterns

### 1. Table Output

```python
def create_result_table(title: str) -> Table:
    """Create a formatted result table."""
    table = Table(title=title, show_header=True)
    table.add_column("Property")
    table.add_column("Value")
    return table
```

### 2. Tree Output

```python
def create_result_tree(root_name: str) -> Tree:
    """Create a formatted result tree."""
    return Tree(f"[bold]{root_name}[/]")
```

## Implementation Guidelines

1. **Command Organization**
   - Group related commands together
   - Use clear, descriptive command names
   - Provide comprehensive help text
   - Include usage examples

2. **Parameter Handling**
   - Validate all parameters
   - Provide clear error messages
   - Use appropriate parameter types
   - Include parameter descriptions

3. **Service Integration**
   - Initialize services during registration
   - Check service availability
   - Handle service errors gracefully
   - Clean up resources when done

4. **Error Management**
   - Catch and handle all exceptions
   - Provide user-friendly error messages
   - Include error context when helpful
   - Log errors appropriately

5. **Result Presentation**
   - Use consistent formatting
   - Support multiple output formats
   - Handle empty/null results
   - Format complex data structures

## Testing Requirements

1. **Command Tests**
   - Test parameter validation
   - Test service integration
   - Test error handling
   - Test output formatting

2. **Integration Tests**
   - Test command registration
   - Test service initialization
   - Test repository integration
   - Test end-to-end workflows

## Security Considerations

1. **Input Validation**
   - Validate all user input
   - Prevent injection attacks
   - Check file permissions
   - Validate UUIDs and paths

2. **Error Messages**
   - Avoid exposing sensitive information
   - Provide appropriate detail level
   - Log security-related errors
   - Handle sensitive data carefully
