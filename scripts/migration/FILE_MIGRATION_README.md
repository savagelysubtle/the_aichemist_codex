# AIchemist Codex File-by-File Migration

This document describes the file-by-file migration approach for the AIchemist Codex codebase restructuring when directory moves fail due to permission issues.

## Process Overview

1. This configuration creates the target directories with __init__.py files
2. After running this configuration, you'll need to manually copy the Python files from each source directory to the corresponding target directory
3. Then update imports in each file to match the new structure

## Migration Steps

1. Run this configuration to create the target structure:
   ```bash
   python scripts/migration/codebase_restructure.py --config scripts/migration/move_files_individually.json
   ```

2. Manually copy Python files from source to target directories:
   - From `backend/core/common` → `core/utils/common`
   - From `backend/core/file_manager` → `core/filesystem/manager`
   - From `backend/core/tagging` → `core/tagging`
   - And so on...

3. Update imports in each file:
   - Change `from the_aichemist_codex.backend` to `from the_aichemist_codex`
   - Change `from the_aichemist_codex.backend.core.file_reader` to `from the_aichemist_codex.core.filesystem`

## Manual Source → Target Mapping

- `backend/core/common` → `core/utils/common`
- `backend/core/file_manager` → `core/filesystem/manager`
- `backend/core/tagging` → `core/tagging`
- `backend/core/search` → `core/analysis/search`
- `backend/core/rollback` → `core/versioning/rollback`
- `backend/core/relationships` → `core/relations`
- `backend/core/project_reader` → `core/ingest/project_reader`
- `backend/core/output_formatter` → `core/output/formatter`
- `backend/core/ingest` → `core/ingest/processor`
