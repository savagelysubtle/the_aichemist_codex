# Data Directory Configuration

## Overview

The Aichemist Codex stores various data files including:

- Backups
- Logs
- Notifications
- Version history
- Cache files
- Exports

This documentation explains how the data directory is configured and how to
customize it.

## Configuration Options

### Environment Variables

You can configure the data directory using these environment variables:

| Variable             | Description                      | Example                  |
| -------------------- | -------------------------------- | ------------------------ |
| `AICHEMIST_ROOT_DIR` | Sets the project root directory  | `C:/Projects/aichemist`  |
| `AICHEMIST_DATA_DIR` | Directly sets the data directory | `C:/Data/aichemist_data` |

Setting `AICHEMIST_DATA_DIR` takes precedence over `AICHEMIST_ROOT_DIR`.

### Automatic Detection

If no environment variables are set, the system uses this detection logic:

1. Look for repository indicators (README.md, pyproject.toml, .git) to find the
   project root
2. Default to the parent directory of the backend folder if no indicators are
   found
3. Use a `data` subdirectory in the detected project root

## Directory Structure

When properly configured, the data directory contains these subdirectories:

```
data/
├── backup/             # File backups for rollback operations
├── cache/              # Temporary cache files
├── exports/            # Exported analysis results
├── logs/               # Application logs
├── notifications/      # Stored notifications
├── trash/              # Deleted files (temporary storage)
└── versions/           # Version history
```

## Validation Tool

The Aichemist Codex includes a validation tool that checks your data directory
configuration. To use it:

```bash
# From the backend directory
python src/tools/validate_data_dir.py
```

This tool:

1. Checks if environment variables are set
2. Identifies the detected project root and data directory
3. Verifies that all required directories exist and are accessible
4. Validates permissions on the directories

If any issues are detected, the tool will display error messages to help you
resolve them.

## Troubleshooting

If you've previously been using the application and switch to a new data
directory:

1. Copy your existing data files to the new location
2. Set the environment variable pointing to the new location
3. Restart the application
4. Run the validation tool to verify your setup

## Migration from Previous Versions

Earlier versions of The Aichemist Codex had two separate data directories:

- `<project_root>/data/`
- `<project_root>/backend/data/`

This has been consolidated into a single data directory. The system now
consistently uses the location specified by the environment variables or
automatically detected using the logic described above.

## Testing the Configuration

The data directory configuration has been thoroughly tested to ensure it works
correctly on different platforms. You can run the tests yourself:

```bash
# From the backend directory
python -m pytest tests/utils/test_data_dir.py -v
```

The tests verify:

1. Environment variable processing works correctly
2. Default paths are used when no environment variables are set

### Setting Environment Variables

#### Windows (Command Prompt)

```
set AICHEMIST_DATA_DIR=C:\custom\data\path
```

#### Windows (PowerShell)

```
$env:AICHEMIST_DATA_DIR = "C:\custom\data\path"
```

#### Linux/macOS

```
export AICHEMIST_DATA_DIR=/custom/data/path
```
