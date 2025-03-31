# AIchemist Codex Test Suite

This directory contains tests for the AIchemist Codex CLI and related functionality.

## Test Structure

The test suite follows the project's clean architecture with tests organized in these layers:

```tests/
├── unit/                    # Unit tests for individual components
│   ├── domain/              # Testing domain entities and value objects
│   ├── application/         # Testing use cases and application services
│   ├── infrastructure/      # Testing infrastructure implementations
│   └── interfaces/          # Testing CLI, API and UI components
├── integration/             # Integration tests between components
│   ├── services/            # Testing service integration
│   ├── api/                 # Testing API integration
│   └── cli/                 # Testing CLI integration with services
├── e2e/                     # End-to-end tests for complete workflows
├── fixtures/                # Test fixtures and factory methods
└── conftest.py              # Common pytest configurations and fixtures
```

## Test Categories

### Unit Tests

Unit tests verify individual components in isolation using mocks and stubs for dependencies. They provide fast feedback on component functionality.

### Integration Tests

Integration tests verify that different components work correctly together. They test the interaction between layers and modules.

### End-to-End Tests

E2E tests verify the application from the user's perspective, testing complete workflows from start to finish.

## Running Tests

To run the tests, use pytest from the project root:

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit
pytest tests/integration
pytest tests/e2e

# Run specific test files
pytest tests/unit/interfaces/cli/test_analysis_commands.py

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=src
```

## Test Fixtures

Common test fixtures are defined in `tests/fixtures/` and in `conftest.py`. These provide reusable test data and utilities.

## Analysis Module Tests

The analysis module tests verify CLI commands for code analysis functionality:

1. **Unit Tests** (`tests/unit/interfaces/cli/test_analysis_commands.py`):
   - Tests individual command functions in isolation
   - Uses mocks to avoid dependencies on filesystem operations
   - Covers error handling and output formats

2. **Integration Tests** (`tests/integration/cli/test_analysis_integration.py`):
   - Tests integration with the analysis infrastructure layer
   - Uses temporary files with real content
   - Validates correct processing of code analysis

3. **End-to-End Tests** (`tests/e2e/test_analysis_cli.py`):
   - Tests the CLI from the user's perspective
   - Validates complete workflows
   - Ensures correct behavior of all commands and options

## Writing New Tests

When adding new features to the CLI, follow these guidelines for test coverage:

1. Write unit tests for each command function
2. Write integration tests for service interactions
3. Write E2E tests for user workflows
4. Use appropriate fixtures for test data
5. Follow the naming conventions:
   - `test_<function_name>` for unit tests
   - `test_<component>_integration` for integration tests
   - `test_<feature>_workflow` for E2E tests

## Detailed Documentation

For more detailed testing guidelines and information about specific test modules, see the [Testing Guide](../docs/development/testing.md).
