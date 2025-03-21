# The AIChemist Codex - Technical Context

## Technologies Used

### Core Technologies

- **Python 3.10+**: Primary programming language
- **asyncio**: For asynchronous operations and concurrency
- **pathlib**: Modern path manipulation
- **typing**: Type hints and annotations

### Dependency Management

- **UV**: Fast Python package resolver and installer
- **pyproject.toml**: Modern project configuration

### Testing Framework

- **pytest**: Testing framework
- **pytest-asyncio**: Testing asynchronous code
- **pytest-cov**: Test coverage reporting
- **pytest-benchmark**: Performance benchmarking

### Code Quality Tools

- **mypy**: Static type checking
- **ruff**: Fast Python linter and code formatter
- **pre-commit**: Git hooks for code quality enforcement
- **coverage**: Test coverage measurement

### Documentation

- **Sphinx**: Documentation generation
- **sphinx-rtd-theme**: Documentation theme
- **autodoc**: Automatic API documentation

## Development Setup

### Environment Setup

```bash
# Clone repository
git clone https://github.com/yourusername/the_aichemist_codex.git
cd the_aichemist_codex

# Set up virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies with Poetry
poetry install

# Or with pip
pip install -e ".[dev]"
```

### Development Tools Configuration

- **.pre-commit-config.yaml**: Configured pre-commit hooks
- **.ruff.toml**: Ruff linter configuration
- **pyproject.toml**: Project configuration including tool settings
- **.python-version**: Python version specification for pyenv
- **.gitignore**: Configured for Python projects
- **Makefile**: Common development tasks

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_file_reader.py

# Run benchmarks
pytest tests/benchmarks/
```

### Code Style & Linting

```bash
# Run mypy type checking
mypy src/

# Run ruff linter
ruff check src/

# Format code with ruff
ruff format src/

# Run all pre-commit hooks
pre-commit run --all-files
```

## Technical Constraints

### Performance Constraints

- **Memory Efficiency**: Handle large file collections without excessive memory
  usage
- **Processing Speed**: Quick response time for search and indexing operations
- **Scalability**: Scale to handle hundreds of thousands of files

### Compatibility Constraints

- **Python Version**: Support Python 3.10 and newer
- **Operating Systems**: Cross-platform support (Windows, macOS, Linux)
- **File Systems**: Work with different file systems and encodings

### Security Constraints

- **Path Traversal Prevention**: Strict path validation to prevent security
  issues
- **Configuration Security**: Secure storage of sensitive configuration
- **Content Isolation**: Safe handling of potentially malicious file content

### Implementation Constraints

- **Pure Python**: Minimize C extension dependencies for easier installation
- **Loose Coupling**: Use interfaces and dependency injection
- **Type Safety**: Strong typing throughout the codebase

## Dependencies

### Core Dependencies

- **PyYAML**: YAML file parsing and generation
- **python-magic**: File type detection
- **chardet**: Character encoding detection
- **rich**: Terminal formatting and display
- **click**: Command-line interface toolkit

### Optional Dependencies

- **numpy**: Numerical operations for advanced features
- **pandas**: Data manipulation for analytics features
- **pillow**: Image processing
- **nltk**: Natural language processing
- **scikit-learn**: Machine learning capabilities

### Development Dependencies

- **pytest**: Testing framework
- **mypy**: Type checking
- **ruff**: Linting and formatting
- **pre-commit**: Git hooks
- **sphinx**: Documentation

## Configuration Management

### Configuration Structure

```
.aichemist/
├── config.yaml           # Main configuration
├── cache/                # Cache directory
├── indexes/              # Search indexes
└── metadata/             # Extracted metadata
```

### Configuration Format

```yaml
# Example configuration
paths:
  data_dir: .aichemist
  cache_dir: .aichemist/cache

search:
  indexer: simple
  max_results: 100

file_types:
  text:
    - .txt
    - .md
    - .py
  document:
    - .pdf
    - .docx
```

## Environment Variables

- **AICHEMIST_CONFIG_PATH**: Path to configuration file
- **AICHEMIST_DATA_DIR**: Data directory override
- **AICHEMIST_LOG_LEVEL**: Logging level (DEBUG, INFO, WARNING, ERROR)
- **AICHEMIST_DISABLE_TELEMETRY**: Disable anonymous usage statistics
