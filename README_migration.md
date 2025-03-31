# AIchemist Codex Migration Tool

This tool automates the process of restructuring the AIchemist Codex codebase by
moving files and updating import statements according to a JSON configuration
file.

## Features

- Loads migration operations from a JSON configuration file
- Handles moving files with automatic directory creation
- Updates import statements in moved files
- Includes retry logic for Windows permission issues
- Provides detailed logging of all operations

## Prerequisites

- Python 3.7 or higher
- The AIchemist Codex project structure

## Usage

```bash
# Using the default configuration (reader_migration_plan.json)
python desktopscript.py

# Specifying a different configuration file
python desktopscript.py --config full_migration_plan.json

# Specifying a different project root
python desktopscript.py --project-root "D:/Projects/the_aichemist_codex"

# Combining options
python desktopscript.py --config full_migration_plan.json --project-root "D:/Projects/the_aichemist_codex"
```

## JSON Configuration Format

The migration configuration is a JSON array of operations, where each operation
is an object with the following properties:

```json
[
  {
    "source": "relative/path/to/source/file.py",
    "destination": "relative/path/to/destination/file.py",
    "imports_to_update": {
      "from old.import": "from new.import",
      "import old.module": "import new.module"
    }
  }
]
```

- `source`: The relative path from the project root to the source file
- `destination`: The relative path from the project root to the destination file
- `imports_to_update`: A dictionary mapping old import statements to new ones

## Available Configuration Files

1. `reader_migration_plan.json` - A minimal configuration for testing or
   migrating a single file
2. `full_migration_plan.json` - A comprehensive plan for migrating all backend
   modules to the new core structure

## Important Notes

- **ALWAYS BACKUP YOUR CODE** before running this script! The script will delete
  source files after moving them.
- Review the migration log file (`migration_log.txt`) after execution to ensure
  all operations were successful.
- If you encounter errors, check that all source paths exist and that you have
  appropriate permissions.
- Consider running a version control (git) commit before running the migration
  to make rollback easier if needed.

## Troubleshooting

### Source files not found

- Check that the paths in your JSON configuration use the correct path format
  (backslashes for Windows)
- Verify that the files exist in the specified source locations
- Make sure the PROJECT_ROOT variable is correctly set to the absolute path of
  your project

### Permission errors

- The script includes retry logic for Windows permission issues, but persistent
  errors may require closing applications that are using the files
- Run the script with appropriate permissions

## Logging

The script creates a detailed log file (`migration_log.txt`) that records all
operations, warnings, and errors. Always check this log after running the script
to ensure all operations were completed successfully.
