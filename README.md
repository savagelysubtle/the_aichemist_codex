# The AIchemist Codex

An intelligent file management and analysis system with advanced content extraction capabilities.

## Architecture

The AIchemist Codex follows clean architecture principles with a clear separation of concerns:

```plaintext
src/the_aichemist_codex/
├── domain/            # Core business logic and entities
│   ├── entities/      # Domain objects with identity and lifecycle
│   ├── value_objects/ # Immutable objects defined by their attributes
│   ├── repositories/  # Repository interfaces for data access
│   ├── services/      # Domain services
│   ├── events/        # Domain events
│   └── exceptions/    # Domain-specific exceptions
│
├── application/       # Orchestrates domain objects to perform tasks
│   ├── use_cases/     # Application-specific business rules
│   ├── commands/      # Operations that change state
│   ├── queries/       # Operations that retrieve data
│   ├── dto/           # Data Transfer Objects
│   ├── mappers/       # Transform between domain objects and DTOs
│   └── services/      # Application services
│
├── infrastructure/    # Implements interfaces defined in inner layers
│   ├── repositories/  # Concrete repository implementations
│   ├── persistence/   # Database access
│   ├── fs/            # File system operations
│   ├── ai/            # AI capabilities and models
│   ├── config/        # Configuration handling
│   └── utils/         # Infrastructure utilities
│
├── interfaces/        # User and external system interaction
│   ├── api/           # API endpoints
│   ├── cli/           # Command-line interface
│   ├── events/        # External event handlers
│   ├── ingest/        # Content ingestion interfaces
│   └── output/        # Output formatting
│
└── cross_cutting/     # Concerns that span multiple layers
    ├── logging/       # Centralized logging
    ├── error_handling/# Error management
    ├── security/      # Authentication and authorization
    ├── validation/    # Input validation
    └── telemetry/     # Performance monitoring and metrics
```

## Configuration

The AIchemist Codex has consolidated most of its configuration files into `pyproject.toml`, following modern Python packaging practices. This reduces configuration clutter and improves tooling support.

For more details on the configuration approach, see the [Configuration Migration Documentation](docs/guides/configuration_migration.rst).

## Getting Started

### Installation

```bash
pip install -e .
```

### Usage

```python
from the_aichemist_codex.infrastructure.fs.file_reader import FileReader
from the_aichemist_codex.interfaces.ingest.scanner import DirectoryScanner
from the_aichemist_codex.application.use_cases.document_analysis import AnalyzeDocumentsUseCase

# Example usage
reader = FileReader()
scanner = DirectoryScanner()
analyzer = AnalyzeDocumentsUseCase()

# Scan a directory
results = scanner.scan('path/to/directory')

# Read files
documents = reader.read_files(results)

# Analyze documents
analysis_results = analyzer.execute(documents)
```

## Development

### Pre-commit Hooks

The project uses pre-commit hooks to enforce code quality standards. Install and set up pre-commit:

```bash
pip install pre-commit
pre-commit install
```

Run the hooks manually:

```bash
pre-commit run --all-files
```

## License

Proprietary
