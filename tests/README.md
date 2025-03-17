# Testing in The Aichemist Codex

This directory contains tests for The Aichemist Codex backend. Tests are
organized into categories based on functionality areas.

## Test Organization

Tests are organized into the following structure:

```
backend/tests/
├── conftest.py        # Common pytest fixtures and configurations
├── __init__.py        # Package initialization
├── run_tests.py       # Main test runner script
├── integration/       # Integration tests that test components working together
└── unit/              # Unit tests for individual components
    ├── cli/           # Tests for command-line interface
    ├── core/          # Tests for core functionality
    ├── content_processing/ # Tests for content parsing and processing
    ├── file_operations/ # Tests for file-related operations
    ├── ingest/        # Tests for data ingestion
    ├── metadata/      # Tests for metadata extractors
    ├── output/        # Tests for output formatting
    ├── relationships/ # Tests for file relationship functionality
    ├── search/        # Tests for search functionality
    ├── simple/        # Simple tests for verifying test setup
    ├── tagging/       # Tests for tagging functionality
    └── utils/         # Tests for utility functions
```

## Running Tests

You can run tests using pytest directly or with our convenient test runner
script.

### Using the Test Runner Script

The `run_tests.py` script provides a convenient way to run tests with different
options:

```bash
# Run all tests
python backend/tests/run_tests.py

# Run only unit tests
python backend/tests/run_tests.py --unit

# Run only metadata tests
python backend/tests/run_tests.py --metadata

# Run tests in verbose mode
python backend/tests/run_tests.py --verbose

# Run tests with coverage report
python backend/tests/run_tests.py --coverage

# Run simple tests (useful for verifying test setup)
python backend/tests/run_tests.py --simple
```

You can combine multiple options:

```bash
# Run unit tests with verbose output and coverage report
python backend/tests/run_tests.py --unit --verbose --coverage
```

### Running Tests with Pytest Directly

You can also run tests using pytest with various options:

#### Running All Tests

```bash
pytest backend/tests
```

#### Running Specific Test Categories

Run tests by module or directory:

```bash
# Run all CLI tests
pytest backend/tests/unit/cli

# Run specific test file
pytest backend/tests/unit/metadata/test_pdf_extractor.py
```

#### Running Tests by Marker

Tests are marked with categories to make it easier to run specific types of
tests:

```bash
# Run all unit tests
pytest -m unit

# Run only metadata tests
pytest -m metadata

# Run tests with multiple markers (AND)
pytest -m "unit and metadata"

# Run tests with either marker (OR)
pytest -m "cli or tagging"

# Exclude slow tests
pytest -m "not slow"
```

### Available Markers

- `unit`: Unit tests
- `integration`: Integration tests
- `metadata`: Tests for metadata extractors
- `tagging`: Tests for tagging functionality
- `search`: Tests for search functionality
- `cli`: Tests for command-line interface
- `slow`: Tests that take longer to run

## Writing New Tests

When adding new tests:

1. Place the test in the appropriate subdirectory under `unit/` or
   `integration/`
2. Use the naming convention `test_*.py` for test files
3. Name test functions as `test_*`
4. Add appropriate pytest markers to categorize your tests
5. Add proper docstrings to explain what the test is checking

Example:

```python
import pytest

@pytest.mark.unit
@pytest.mark.metadata
def test_new_feature():
    """Test that the new feature works as expected."""
    # Test code here
    assert True
```

## Known Issues and Troubleshooting

### Circular Imports

There are circular import issues in the codebase that need to be addressed. The
most common error is:

```
ImportError: cannot import name 'directory_monitor' from partially initialized module 'backend.src.file_manager.directory_monitor'
```

This is caused by circular dependencies between modules, particularly in the
`file_manager` package. To fix this:

1. Refactor the imports in the affected modules
2. Move shared functionality to a separate module
3. Use import statements inside functions rather than at the module level

### Async Test Syntax

Many test files have syntax errors with async tests. The correct syntax for
async tests is:

```python
@pytest.mark.asyncio
@pytest.mark.unit
async def test_async_function():
    """Test an async function."""
    # Test code here
    result = await some_async_function()
    assert result is not None
```

The incorrect syntax that appears in many files is:

```python
async @pytest.mark.unit  # This is invalid syntax
def test_async_function():
    # ...
```

### Missing Dependencies

Some tests fail due to missing dependencies:

- `ModuleNotFoundError: No module named 'pyaudioop'` - This is related to the
  `pydub` library
- `ModuleNotFoundError: No module named 'audioop'` - This is related to audio
  processing
- `ModuleNotFoundError: No module named 'backend.src.scipy'` - This is related
  to scientific computing

To fix these issues:

1. Install the required dependencies:

   ```bash
   pip install scipy
   ```

2. For audio-related dependencies, you may need to install system packages:
   - On Windows: Install the appropriate Python audio libraries
   - On Linux: `sudo apt-get install python3-dev libasound2-dev`

### Example Tests

The `unit/simple` and `unit/metadata/test_metadata_example.py` files provide
working examples of how to write tests that don't depend on problematic imports.
Use these as templates when creating new tests.
