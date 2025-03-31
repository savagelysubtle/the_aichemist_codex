# AIchemist Codex File Migration

This document describes the file migration process for the AIchemist Codex codebase restructuring.

## Process Overview

1. Execute the `move_files.json` configuration with the `codebase_restructure.py` script to migrate existing files to the new structure.
2. This approach focuses on preserving existing code by moving files rather than creating duplicates.

## Migration Commands

```bash
# Run a dry-run to verify the file migrations before applying
python scripts/migration/codebase_restructure.py --config scripts/migration/move_files.json --dry-run

# Execute the file migrations
python scripts/migration/codebase_restructure.py --config scripts/migration/move_files.json
```

## Structure Overview

The migration process moves files to these logical modules while preserving functionality:

- **Core**: Central domain logic and models
  - **filesystem**: Contains FileMetadata and FileReader from the original file_reader module
  - **parsing**: Contains parsers from the original file_reader module
  - **extraction**: Contains metadata extraction functionality from the original metadata module
  - **utils**: Utility functions and helpers

## Next Steps

1. Test the codebase after migration to ensure functionality is maintained
2. Continue migrating additional modules as needed
3. Update import references in other parts of the codebase
