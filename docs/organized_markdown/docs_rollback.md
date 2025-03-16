Here's the updated content for modules/rollback.md:

```markdown
# Rollback Package Documentation

## Overview
The Rollback package provides a robust system for tracking, undoing, and redoing file operations with backup management. It implements a singleton pattern for consistent operation tracking across the application, with asynchronous I/O operations and comprehensive error handling.

## Components

### 1. Rollback Manager (rollback_manager.py)
- Core rollback functionality
- Features:
  - Operation tracking
  - Undo/redo capabilities
  - Backup management
  - Trash handling
  - Asynchronous operations
- Example usage:
  ```python
  # Record an operation
  await rollback_manager.record_operation("move", source_path, dest_path)

  # Undo last operation
  success = await rollback_manager.undo_last_operation()

  # Redo last undone operation
  success = await rollback_manager.redo_last_undone()
  ```

### 2. Rollback Operation

- Operation tracking class
- Attributes:
  - operation: Type of operation
  - source: Original file path
  - destination: Target path (if applicable)
  - timestamp: Operation time
  - backup: Backup file path
- Supported operations:
  - move
  - delete
  - create
  - rename
  - modify

## Implementation Details

### Operation Recording

```python
{
    "timestamp": 1678450123.25,
    "operation": "move",
    "source": "/path/to/original_file.txt",
    "destination": "/path/to/target_dir/original_file.txt",
    "backup": "/path/to/backup/file.bak"
}
```

### Directory Structure

- TRASH_DIR: For deleted files
- BACKUP_DIR: For file backups
- DATA_DIR: For rollback logs

### Key Features

#### 1. Operation Tracking

- Persistent operation logging
- JSON-based storage
- Timestamp tracking
- Operation metadata

#### 2. Backup Management

- Automatic file backups
- Backup verification
- Cleanup capabilities
- Retention policies

#### 3. Undo/Redo System

- Operation reversal
- State tracking
- Error recovery
- Operation verification

#### 4. Trash Management

- File preservation
- Restore capabilities
- Retention policies
- Automatic cleanup

## Integration Points

### Internal Dependencies

- Config package for settings
- Utils package for async I/O
- Logger for operation tracking

### External Dependencies

- asyncio for async operations
- pathlib for path handling
- json for log storage

## Best Practices

### Recording Operations

```python
# Record a move operation
await rollback_manager.record_operation(
    operation="move",
    source="/path/to/source.txt",
    destination="/path/to/dest.txt"
)

# Record a deletion
await rollback_manager.record_operation(
    operation="delete",
    source="/path/to/file.txt"
)
```

### Managing Backups

```python
# Restore from trash
success = await rollback_manager.restore_from_trash("file.txt")

# Clear old trash files
await rollback_manager.clear_trash()

# Clean up old entries
await rollback_manager.cleanup_old_entries(retention_days=7.0)
```

### Error Handling

```python
try:
    success = await rollback_manager.undo_last_operation()
    if not success:
        logger.error("Undo operation failed")
except Exception as e:
    logger.error(f"Error during rollback: {e}")
```

## Safety Features

### Operation Safety

- Retry logic for operations
- Backup verification
- Path validation
- Error recovery

### Data Protection

- Automatic backups
- Operation logging
- File preservation
- Trash system

### Error Handling

- Comprehensive logging
- Operation verification
- Recovery mechanisms
- Retry capabilities

## Future Improvements

### Short-term

1. Enhanced backup compression
2. Operation batching
3. Improved error recovery
4. Extended metadata tracking
5. Better cleanup strategies

### Long-term

1. Distributed operation tracking
2. Advanced backup management
3. Operation optimization
4. Cloud backup integration
5. Machine learning-based cleanup

```

This documentation accurately reflects the current implementation while providing clear examples and usage patterns. It covers all major components and their interactions, making it easier for developers to understand and use the rollback system effectively.

