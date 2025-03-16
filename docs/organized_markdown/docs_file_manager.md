# File Manager Package Documentation

## Overview

The File Manager package provides comprehensive file system operations with
asynchronous I/O, safe file handling, directory monitoring, and intelligent file
organization capabilities. It implements robust error handling, rollback
support, and rule-based file sorting.

## Components

### 1. File Tree Generator (file_tree.py)

- Generates hierarchical file system representations
- Features:
  - Asynchronous directory scanning
  - Maximum depth protection (10 levels)
  - Safe file handling with ignore patterns
  - Size tracking for files
  - Comprehensive error handling
- Example output structure:

  ```python
  {
      "directory_name": {
          "file.txt": {"size": 1024, "type": "file"},
          "subdirectory": {...}
      }
  }
  ```

### 2. File Mover (file_mover.py)

- Handles safe file movement operations
- Features:
  - Asynchronous file operations
  - Rollback support for all operations
  - Rule-based file organization
  - Automatic folder structure creation
  - Date-based organization (YYYY-MM)
- Key methods:

  ```python
  async def move_file(source: Path, destination: Path)
  async def apply_rules(file_path: Path)
  async def auto_folder_structure(file_path: Path)
  ```

### 3. Directory Manager (directory_manager.py)

- Manages directory operations safely
- Features:
  - Asynchronous directory creation
  - Empty directory cleanup
  - Rollback support for directory operations
  - Permission validation
- Key methods:

  ```python
  async def ensure_directory(directory: Path)
  async def cleanup_empty_dirs(directory: Path)
  ```

### 4. File Watcher (file_watcher.py)

- Monitors file system changes in real-time
- Features:
  - Event-based file monitoring
  - Debounced file processing (2-second interval)
  - Multiple directory monitoring
  - Automatic file organization
  - Background sorting thread
  - Enhanced event handling (creation, modification, deletion, move/rename)
  - Change severity classification
  - Smart debounce logic
- Implementation details:
  - Uses Python underscore convention for unused variables (e.g.,
    `for dir_path, _ in directory_monitor.directories.items()`)
  - Properly handles scheduled sorting with optimized resource usage
  - Change history tracking with cleanup policy

### 5. Directory Monitor (directory_monitor.py)

- Enhanced directory monitoring capabilities
- Features:
  - Priority-based monitoring (critical, high, normal, low)
  - Resource throttling for high-change-rate directories
  - Recursive directory discovery with customizable depth
  - Dynamic directory registration/unregistration
- Configuration options:

  ```python
  dir_config = DirectoryConfig(
      path=path,
      priority=DirectoryPriority.HIGH,
      recursive_depth=3,
      throttle=1.0,
  )
  ```

### 6. Change Detector (change_detector.py)

- Identifies and classifies file changes
- Features:
  - Content-based detection for text files
  - Hash-based detection for binary files
  - Smart debounce logic
  - Change severity classification (minor, moderate, major, critical)
  - File type detection

### 7. Change History Manager (change_history_manager.py)

- Stores and manages file change history
- Features:
  - SQLite database backend
  - Query API for change history
  - Cleanup policies for old records
  - Change statistics and analytics

### 8. Rule-Based Sorter (sorter.py)

- Implements intelligent file organization
- Features:
  - YAML-based rule configuration
  - Pattern matching
  - Extension filtering
  - Size-based rules
  - Date-based rules
  - Content keyword matching
- Rule criteria:

  ```yaml
  rules:
    - pattern: '*.txt'
      extensions: ['.txt']
      min_size: 1024
      max_size: 1048576
      created_after: '2024-01-01'
      created_before: '2024-12-31'
      keywords: ['important', 'urgent']
      target_dir: 'organized/documents'
  ```

## Implementation Details

### Asynchronous Operations

- Uses `asyncio` for non-blocking I/O
- Implements thread-safe operations
- Handles concurrent file operations
- Provides synchronous wrappers when needed

### Safety Features

- File operation validation
- Permission checking
- Path sanitization
- Duplicate handling
- Error recovery
- Comprehensive logging

### Rollback Support

- Transaction-like file operations
- Operation history tracking
- Automatic rollback on failures
- Directory creation/deletion tracking

### File Organization

- Rule-based sorting
- Automatic folder structure
- Date-based organization
- Extension-based sorting
- Size-based organization
- Content-based sorting

## Integration Points

### Internal Dependencies

- Config package for settings
- Utils package for common operations
- Rollback package for operation tracking
- File Reader for content analysis

### External Dependencies

- watchdog for file system monitoring
- PyYAML for rule configuration
- Python's pathlib for path operations
- asyncio for asynchronous operations

## Testing

The package includes comprehensive tests:

- test_file_tree.py
- test_file_mover.py
- test_directory_manager.py
- test_file_watcher.py
- test_sorter.py

## Best Practices

### File Operations

```python
# Safe file movement
await file_mover.move_file(source_path, target_path)

# Directory creation
await directory_manager.ensure_directory(new_dir_path)

# File watching
monitor_directory()

# Rule-based sorting
sorter = RuleBasedSorter()
await sorter.sort_directory(directory_path)
```

### Python Conventions

```python
# Using underscore for unused variables (PEP 8 recommended)
for dir_path, _ in directory_monitor.directories.items():
    # Process only the directory path, ignoring the configuration value
    process_directory(dir_path)
```

### Error Handling

```python
try:
    await file_mover.move_file(source, destination)
except Exception as e:
    logger.error(f"Error moving file: {e}")
    await rollback_manager.rollback()
```

## Future Improvements

### Short-term

1. Enhanced file type detection
2. Improved duplicate handling
3. More sophisticated sorting rules
4. Better progress tracking
5. Extended metadata support

### Long-term

1. Distributed file operations
2. Machine learning-based file organization
3. Content-based deduplication
4. Real-time synchronization
5. Cloud storage integration

## Future Roadmap

### Phase 2: Feature Enhancements

- Intelligent auto-tagging using NLP
- File relationship mapping
- Real-time change tracking
- File versioning system

### Phase 3: AI Integration

- ML-based file classification
- Pattern recognition
- Anomaly detection
- Smart recommendations

### Phase 4: External Integration

- Cloud storage support
- Synchronization
- API endpoints
- Plugin system
