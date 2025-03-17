# Data Directory Structure

## Overview

This document describes the standardized data directory structure used in The
Aichemist Codex. The data directory is a central location for all persistent
data created and managed by the application.

## Standard Structure

The data directory follows a standard structure:

```
data/
├── cache/          # Temporary cached data
├── logs/           # Application logs
├── versions/       # Version history data
├── exports/        # Exported files
├── backup/         # Backup data
├── trash/          # Recently deleted files
├── rollback.json   # Rollback information
└── version_metadata.json  # Version tracking metadata
```

## Directory Purposes

### 1. `cache/`

The cache directory stores temporary data that can be regenerated if needed.
This includes:

- Search index caches
- Processed file previews
- Temporary computational results
- Any data that improves performance but isn't critical

Cache data may be automatically cleaned up or expired based on time or storage
constraints.

### 2. `logs/`

The logs directory contains application logs, including:

- Operation logs
- Error logs
- Debug information
- Performance metrics

Logs are rotated and archived automatically to prevent excessive disk usage.

### 3. `versions/`

The versions directory stores historical versions of files managed by the
system:

- File snapshots taken before operations
- Version history for tracked files
- State information for version comparison

### 4. `exports/`

The exports directory contains files generated for external use:

- Report exports
- Data exports
- Visualization outputs
- Any other user-requested exported content

### 5. `backup/`

The backup directory stores important backup data:

- System configuration backups
- Critical data backups
- Recovery points

Unlike the versions directory which focuses on file-level history, backups are
typically system-wide or configuration-focused.

### 6. `trash/`

The trash directory temporarily stores deleted files before permanent removal:

- Recently deleted files
- Files marked for deletion but available for recovery
- Metadata for deleted items

This provides a safety mechanism allowing for file recovery.

## Key Files

### `rollback.json`

This file maintains information about operations that can be undone, including:

- Operation type
- Affected files
- Timestamp
- Required actions for rollback

### `version_metadata.json`

This file tracks version history metadata:

- File mappings to versions
- Version timestamps
- User information for changes
- Change descriptions

## Configuring Data Directory Location

### Environment Variables

You can customize the data directory location using environment variables:

- `AICHEMIST_DATA_DIR`: Override the base data directory
- `AICHEMIST_CACHE_DIR`: Override just the cache directory
- `AICHEMIST_LOG_DIR`: Override just the logs directory

### Configuration in Settings

Data directory settings are managed through the `DirectoryManager` class, which:

- Provides a centralized approach to directory access
- Ensures all required directories exist
- Handles OS-specific paths
- Supports environment variable overrides

## CLI Management

Manage the data directory using the CLI:

```bash
# Validate data directory structure
codex data validate

# Repair any issues with the data directory
codex data repair

# View information about data directories
codex data info
```

## Best Practices

1. **Never directly modify** the data directory structure manually
2. **Use the API or CLI** for all data directory operations
3. **Backup regularly**, especially before major operations
4. **Clean the cache** periodically to free up disk space
5. **Monitor logs** for errors or anomalies
