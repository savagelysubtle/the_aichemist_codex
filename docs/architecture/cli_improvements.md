# CLI Architecture Improvements

## Current State

The CLI implementation currently has:

- Basic command structure using Typer
- Command groups for different functionality
- Basic error handling
- Service initialization
- Output formatting

## Proposed Improvements

### 1. Service Management

#### Current Implementation

```python
# Global service references
_service: ServiceInterface | None = None
_repository: Repository | None = None

def register_commands(app: typer.Typer, cli: Any) -> None:
    global _service, _repository
    _repository = Repository()
    _service = Service(_repository)
```

#### Improved Implementation

```python
class CommandContext:
    """Context manager for command services."""
    def __init__(self, config: dict):
        self.config = config
        self._services: dict[str, Any] = {}

    def get_service(self, service_type: type) -> Any:
        """Get or create a service instance."""
        if service_type not in self._services:
            self._services[service_type] = self._create_service(service_type)
        return self._services[service_type]

    def _create_service(self, service_type: type) -> Any:
        """Create a new service instance."""
        return service_type(self.config)

# Usage in commands
@command_group.command()
def command(ctx: typer.Context):
    service = ctx.obj.get_service(ServiceType)
```

### 2. Command Organization

#### Current Implementation

- Commands grouped by functionality
- Some duplication in validation and error handling
- Mixed responsibility in command functions

#### Improved Implementation

```python
class CommandBase:
    """Base class for command implementation."""
    def __init__(self, context: CommandContext):
        self.context = context

    def validate(self) -> None:
        """Validate command parameters."""
        raise NotImplementedError

    def execute(self) -> Any:
        """Execute command logic."""
        raise NotImplementedError

    def display_result(self, result: Any) -> None:
        """Display command results."""
        raise NotImplementedError

class AnalyzeCommand(CommandBase):
    """Example command implementation."""
    def validate(self) -> None:
        # Command-specific validation
        pass

    def execute(self) -> Any:
        # Command-specific execution
        pass

    def display_result(self, result: Any) -> None:
        # Command-specific display logic
        pass
```

### 3. Error Handling

#### Current Implementation

```python
try:
    # Command logic
except Exception as e:
    if _cli is not None:
        _cli.handle_error(e)
    else:
        console.print(f"[bold red]Error:[/] {str(e)}")
```

#### Improved Implementation

```python
class CLIError(Exception):
    """Base class for CLI errors."""
    def __init__(self, message: str, context: dict | None = None):
        super().__init__(message)
        self.context = context or {}

class ValidationError(CLIError):
    """Validation error with context."""
    pass

class ServiceError(CLIError):
    """Service-related error with context."""
    pass

def handle_error(error: Exception) -> None:
    """Enhanced error handling with context."""
    if isinstance(error, CLIError):
        display_contextual_error(error)
    elif isinstance(error, ValueError):
        display_validation_error(error)
    else:
        display_unexpected_error(error)

    # Log error with appropriate level
    log_error(error)
```

### 4. Output Formatting

#### Current Implementation

- Fixed output formats (table, json)
- Limited customization options
- Hardcoded formatting logic

#### Improved Implementation

```python
class OutputFormatter:
    """Flexible output formatting."""
    def __init__(self, format_type: str, options: dict | None = None):
        self.format_type = format_type
        self.options = options or {}

    def format(self, data: Any) -> str:
        """Format data according to type and options."""
        formatter = self._get_formatter()
        return formatter(data)

    def _get_formatter(self) -> Callable:
        """Get appropriate formatter function."""
        return {
            'table': self._format_table,
            'json': self._format_json,
            'tree': self._format_tree,
            'text': self._format_text
        }[self.format_type]

# Usage in commands
@command_group.command()
def command(
    ctx: typer.Context,
    format: str = typer.Option('table', help='Output format')
):
    formatter = OutputFormatter(format)
    result = execute_command()
    formatted_output = formatter.format(result)
    console.print(formatted_output)
```

### 5. Testing Infrastructure

#### Current Implementation

- Basic unit tests
- Limited integration testing
- Manual command testing

#### Improved Implementation

```python
class CommandTester:
    """Test infrastructure for commands."""
    def __init__(self):
        self.app = typer.Typer()
        self.context = TestCommandContext()

    def execute(self, command: str, *args, **kwargs) -> CommandResult:
        """Execute command with args and capture result."""
        result = self.app.invoke(command, *args, **kwargs)
        return CommandResult(
            exit_code=result.exit_code,
            output=result.output,
            exception=result.exception
        )

# Usage in tests
def test_command():
    tester = CommandTester()
    result = tester.execute('analyze', 'test.py', '--depth=2')
    assert result.exit_code == 0
    assert 'Analysis complete' in result.output
```

## Implementation Plan

1. **Phase 1: Service Management**
   - Implement CommandContext
   - Migrate services to context
   - Update command registration

2. **Phase 2: Command Structure**
   - Create CommandBase
   - Migrate existing commands
   - Implement validation framework

3. **Phase 3: Error Handling**
   - Implement error hierarchy
   - Create error handlers
   - Update logging integration

4. **Phase 4: Output Formatting**
   - Implement OutputFormatter
   - Add new format types
   - Update command output

5. **Phase 5: Testing**
   - Implement CommandTester
   - Create test fixtures
   - Add integration tests

## Migration Strategy

1. **Preparation**
   - Create new command structure
   - Set up testing infrastructure
   - Document migration process

2. **Command Migration**
   - Migrate one command group at a time
   - Update tests for each group
   - Verify functionality

3. **Service Migration**
   - Move services to CommandContext
   - Update service initialization
   - Test service integration

4. **Cleanup**
   - Remove old implementations
   - Update documentation
   - Verify all functionality

## Success Criteria

1. **Code Quality**
   - Reduced code duplication
   - Improved error handling
   - Better service management

2. **Testing**
   - Comprehensive test coverage
   - Automated integration tests
   - Easy command testing

3. **User Experience**
   - Consistent error messages
   - Flexible output formats
   - Better command organization

4. **Maintainability**
   - Clear command structure
   - Easy to add new commands
   - Well-documented patterns
