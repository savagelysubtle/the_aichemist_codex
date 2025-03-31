# The AIchemist Codex

An intelligent file management and analysis system with advanced content extraction capabilities.

## New Architecture

The AIchemist Codex has been restructured to follow clean architecture principles with a clear separation of concerns:

```plaintext
src/the_aichemist_codex/
├── core/              # Core domain models and interfaces
├── fs/                # File system operations
├── parsing/           # File content parsing
├── extraction/        # Content extraction and metadata
├── versioning/        # Version control
├── analysis/          # Project analysis
├── relations/         # Relationship management
├── tagging/           # Tagging functionality
├── ingest/            # Content ingestion
├── output/            # Output formatting
├── utils/             # Utility functions
└── config/            # Configuration handling
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
from the_aichemist_codex.fs.file_reader import FileReader
from the_aichemist_codex.ingest.scanner import DirectoryScanner

# Example usage
reader = FileReader()
scanner = DirectoryScanner()

# Scan a directory
results = scanner.scan('path/to/directory')

# Read files
metadata = reader.read_files(results)
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
