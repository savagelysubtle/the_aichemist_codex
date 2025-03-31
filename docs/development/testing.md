# Testing Guide for AIchemist Codex

This document provides comprehensive guidelines for testing the AIchemist Codex project, with a specific focus on the CLI implementation.

## Testing Philosophy

The AIchemist Codex follows these testing principles:

1. **Test-Driven Development (when possible)**: Write tests before implementing features.
2. **Clean Tests**: Tests should be readable, maintainable, and reliable.
3. **Appropriate Coverage**: Different types of tests for different scenarios.
4. **Fast Feedback**: Unit tests provide quick feedback during development.
5. **Realistic Testing**: Integration and E2E tests verify real-world behavior.

## Test Categories

### Unit Tests

Unit tests verify individual components in isolation, using mocks and stubs for dependencies.

**Location**: `tests/unit/`

**Characteristics**:
- Fast execution
- No external dependencies (database, filesystem, network)
- Focus on a single component's behavior
- Heavy use of mocks and test doubles

**When to use**:
- Testing business logic
- Testing component-specific functionality
- Testing error handling and edge cases

### Integration Tests

Integration tests verify that different components work correctly together.

**Location**: `tests/integration/`

**Characteristics**:
- Test interactions between real components
- Minimal mocking (only external services if needed)
- Focus on component interactions and contracts
- May use test databases or filesystem

**When to use**:
- Testing interactions between layers
- Testing infrastructure implementations
- Testing service integrations

### End-to-End Tests

E2E tests verify the application from the user's perspective.

**Location**: `tests/e2e/`

**Characteristics**:
- Test the complete system
- No mocking (except external services)
- Focus on user workflows and scenarios
- Use the application's public interfaces

**When to use**:
- Testing complete workflows
- Testing user interactions
- Testing system integration

## Test Structure

Each test file should follow this general structure:

```python
"""Test module docstring describing what is being tested."""

# Imports

# Test fixtures (if not imported from fixtures or conftest)

# Helper functions (if needed)

# Test functions or classes

# Test cleanup (if needed)
```

## Test Fixtures

Common test fixtures are defined in `tests/fixtures/` and in `conftest.py`.

- **Unit Test Fixtures**: Mock objects, sample data, simple test cases
- **Integration Test Fixtures**: Test database setups, service configurations
- **E2E Test Fixtures**: Test user configurations, application setups

## Analysis Module Test Details

### Unit Tests

File: `tests/unit/interfaces/cli/test_analysis_commands.py`

These tests focus on the individual command functions in the analysis module:

1. **Fixtures**:
   - `mock_console`: Mocks the Rich console for output testing
   - `mock_summarize_code`: Mocks the code summarization function
   - `mock_process_file`: Mocks the file processing function
   - `cli_runner`: Provides a Typer CLI runner for command tests

2. **Command Registration Tests**:
   - `test_register_commands`: Verifies that commands are correctly registered with the CLI app

3. **Scan Command Tests**:
   - `test_scan_nonexistent_directory`: Tests error handling when the directory doesn't exist
   - `test_scan_with_table_output`: Tests the default table output format
   - `test_scan_with_json_output`: Tests the JSON output format

4. **File Analysis Tests**:
   - `test_analyze_nonexistent_file`: Tests error handling when the file doesn't exist
   - `test_analyze_non_python_file`: Tests validation of Python file extensions
   - `test_analyze_file_with_docstrings`: Tests the docstring display functionality

**Expected Outcomes**:
- Command registration correctly sets up CLI instance
- Non-existent paths trigger appropriate errors
- Output formats correctly process and display data
- File validation correctly identifies issues

### Integration Tests

File: `tests/integration/cli/test_analysis_integration.py`

These tests focus on the integration between CLI commands and analysis infrastructure:

1. **Fixtures**:
   - `sample_python_file`: Creates a temporary Python file with test content
   - `mock_cli`: Creates a mock CLI instance for error handling

2. **Integration Tests**:
   - `test_scan_code_integration`: Tests integration with the summarize_code function
   - `test_file_analysis_integration`: Tests integration with the process_file function
   - `test_output_formats_integration`: Tests different output formats with real data

**Expected Outcomes**:
- Code analysis correctly extracts functions and classes
- File analysis correctly processes Python files
- Output formatting correctly renders in different formats

### End-to-End Tests

File: `tests/e2e/test_analysis_cli.py`

These tests focus on the complete CLI workflow:

1. **Fixtures**:
   - `cli_runner`: Provides a Typer CLI runner
   - `sample_project`: Creates a temporary project with Python files

2. **E2E Tests**:
   - `test_analysis_scan_command`: Tests the full scan command workflow
   - `test_analysis_scan_with_json_format`: Tests JSON output in the full workflow
   - `test_analysis_file_command`: Tests file analysis from the CLI
   - `test_analysis_file_without_docstrings`: Tests disabling docstrings
   - `test_analysis_file_nonexistent`: Tests error handling for missing files
   - `test_analysis_complexity_command`: Tests the stub for complexity analysis
   - `test_analysis_dependencies_command`: Tests the stub for dependency analysis

**Expected Outcomes**:
- CLI commands execute successfully
- Output contains expected information
- Error handling works correctly
- Options and flags modify behavior as expected

## Running the Tests

To run the analysis module tests:

```bash
# Run all analysis tests
pytest tests/unit/interfaces/cli/test_analysis_commands.py tests/integration/cli/test_analysis_integration.py tests/e2e/test_analysis_cli.py

# Run specific test categories
pytest tests/unit/interfaces/cli/test_analysis_commands.py
pytest tests/integration/cli/test_analysis_integration.py
pytest tests/e2e/test_analysis_cli.py

# Run a specific test
pytest tests/unit/interfaces/cli/test_analysis_commands.py::test_register_commands
```

## Test Dependencies

The analysis module tests depend on:

1. **pytest**: Testing framework
2. **typer**: CLI framework with testing utilities
3. **rich**: Output formatting and console capture
4. **unittest.mock**: Mocking functionality

## Troubleshooting Tests

### Common Issues

1. **Import Errors**:
   - Ensure pytest is installed in your environment
   - Check for correct import paths

2. **File Not Found Errors**:
   - Check that test fixtures create files in the expected locations
   - Ensure paths are correct for your operating system

3. **Assertion Failures**:
   - Check expected vs. actual values in test output
   - Verify that mocks return the expected data

## Extending Tests

When adding new commands to the analysis module:

1. Add unit tests for the new command function
2. Add integration tests for any infrastructure integration
3. Add E2E tests for the complete CLI workflow
4. Update any shared fixtures as needed

## Code Coverage

Aim for high test coverage, especially for:

1. Command logic and parameter handling
2. Error cases and validation
3. Output formatting and display
4. Integration with infrastructure services
