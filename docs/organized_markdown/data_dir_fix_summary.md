# Data Directory Fix Summary

## Issues Addressed

1. **Duplicate Data Directories**: The project had two separate data
   directories:

   - Root data directory: `<project_root>/data/`
   - Backend data directory: `<project_root>/backend/data/`

2. **Inconsistent Path Calculation**: The previous path calculation in
   `settings.py` could lead to inconsistent behavior:
   ```python
   ROOT_DIR = Path(__file__).parent.parent.parent
   DATA_DIR = ROOT_DIR / "data"
   ```

## Changes Made

### 1. Enhanced Directory Resolution

Updated `settings.py` to use a more robust approach for determining directories:

```python
def determine_project_root() -> Path:
    """
    Determine the project root directory using multiple methods.

    First checks for environment variable, then tries to detect based on
    repository structure, with a fallback to the parent of the backend directory.
    """
    # Check environment variable first
    env_root = os.environ.get("AICHEMIST_ROOT_DIR")
    if env_root:
        root_dir = Path(env_root).resolve()
        if root_dir.exists():
            return root_dir

    # Look for repository indicators
    current_file = Path(__file__).resolve()
    potential_root = current_file.parent.parent.parent.parent

    # Check for indicators of project root (like README.md, pyproject.toml, etc.)
    root_indicators = ["README.md", "pyproject.toml", ".git"]
    if any((potential_root / indicator).exists() for indicator in root_indicators):
        return potential_root

    # Fallback to parent of backend directory
    return current_file.parent.parent.parent
```

### 2. Environment Variable Support

Added support for environment variables to allow flexible configuration:

- `AICHEMIST_ROOT_DIR`: Override the project root directory
- `AICHEMIST_DATA_DIR`: Directly set the data directory (takes precedence)

### 3. Comprehensive Documentation

Created detailed documentation:

- `docs/data_directory_config.md`: Explains configuration options and directory
  structure
- Updated `docs/configuration.rst`: Added data directory section to main
  configuration docs

### 4. Validation and Testing

Added tools to validate and test the configuration:

- `backend/src/tools/validate_data_dir.py`: Validates the current data directory
  setup
- `backend/tests/utils/test_data_dir.py`: Pytest tests to verify the
  configuration logic

## Migration Path

The changes have been implemented to maintain backward compatibility while
providing a clear path for migration:

1. Existing code that relies on `DATA_DIR` will continue to work
2. New environment variables allow for explicit configuration
3. Documentation explains the directory structure and migration process
4. The validation tool helps users verify their setup

## Benefits

1. **Consistency**: Single source of truth for data location
2. **Configurability**: Environment variables for flexible deployment
3. **Robustness**: Better path detection across different environments
4. **Testability**: Unit tests ensure the configuration works correctly
5. **Discoverability**: Validation tool helps users understand the configuration
