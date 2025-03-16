# File Versioning System

## Overview

The File Versioning System is a core component of The Aichemist Codex that
provides automated tracking and management of file changes over time. It creates
and maintains multiple versions of files, allowing users to track changes,
compare different versions, and restore previous states when needed.

The system offers configurable versioning policies, intelligent storage
optimization, and seamless integration with the file watching and change
detection systems.

## Key Features

- **Automated Version Creation**: Automatically creates versions when files are
  modified, moved, or when significant changes are detected
- **Flexible Versioning Policies**: Supports different versioning strategies
  (full copies, diff-based, or hybrid) optimized for different file types
- **Storage Optimization**: Uses differential storage for text files to minimize
  disk usage
- **Version Management**: Maintains metadata about each version including
  timestamps, authors, and change reasons
- **Version Restoration**: Allows restoring files to any previous version
- **Cleanup Management**: Automatically prunes old versions based on
  configurable retention policies

## Configuration

The versioning system is highly configurable through both the `settings.py` file
and the `.codexconfig` file.

### Default Settings (settings.py)

```python
DEFAULT_VERSIONING_SETTINGS = {
    "auto_create_versions": True,  # Automatically create versions on file changes
    "version_on_modify": True,     # Create versions when files are modified
    "max_versions_per_file": 20,   # Maximum number of versions to keep per file
    "default_policy": "HYBRID",    # Default versioning policy (FULL_COPY, DIFF_BASED, HYBRID)
    "version_retention_days": 30,  # Number of days to keep versions before cleanup
    "compression_enabled": True,   # Use compression for stored versions
    "include_patterns": [          # File patterns to include in versioning
        "*.py", "*.js", "*.ts", "*.html", "*.css", "*.md", "*.txt",
        "*.json", "*.yaml", "*.yml", "*.xml", "*.csv", "*.sql",
    ],
    "exclude_patterns": [          # File patterns to exclude from versioning
        "*.log", "*.tmp", "*.temp", "*.swp", "*.bak", "*.backup",
        "*.pyc", "*.class", "*.o", "*.obj",
    ],
}
```

### User Configuration (.codexconfig)

You can customize the versioning behavior in the `.codexconfig` file:

```toml
[versioning]
# Whether to automatically create versions when files change
auto_create_versions = true

# Create versions when files are modified (vs. only on creation or specific operations)
version_on_modify = true

# Maximum number of versions to keep per file
max_versions_per_file = 20

# Default versioning policy (FULL_COPY, DIFF_BASED, HYBRID)
default_policy = "HYBRID"

# Number of days to keep versions before cleanup
version_retention_days = 30

# Use compression for stored versions to save space
compression_enabled = true

# File patterns to include in versioning (glob patterns)
include_patterns = [
    "*.py", "*.js", "*.ts", "*.html", "*.css", "*.md", "*.txt",
    "*.json", "*.yaml", "*.yml", "*.xml", "*.csv", "*.sql"
]

# File patterns to exclude from versioning (glob patterns)
exclude_patterns = [
    "*.log", "*.tmp", "*.temp", "*.swp", "*.bak", "*.backup",
    "*.pyc", "*.class", "*.o", "*.obj"
]
```

## Versioning Policies

The system supports three versioning policies:

1. **FULL_COPY**: Stores complete file copies for each version. This is the most
   straightforward approach and works with all file types, but uses more
   storage.

2. **DIFF_BASED**: Stores only the differences between versions for text files
   using unified diff format. This is space-efficient but only works well with
   text files.

3. **HYBRID** (default): Uses diff-based storage for text files and full copies
   for binary files. This provides a good balance between storage efficiency and
   compatibility.

## API Reference

### VersionManager

The `VersionManager` is the main class that handles all versioning operations.

```python
from backend.src.file_manager.version_manager import version_manager
```

#### Creating Versions

```python
version_id = await version_manager.create_version(
    file_path,  # Path to the file to version
    change_reason="Manually saved version",  # Optional reason for the version
    author="User",  # Optional author name
    policy=None  # Optional versioning policy override
)
```

#### Listing Versions

```python
# Get all versions for a file
versions = await version_manager.list_versions(file_path)
for version in versions:
    print(f"Version: {version.version_id}, Created: {version.timestamp}, Author: {version.author}")
```

#### Getting Version Information

```python
# Get detailed information about a specific version
version_info = await version_manager.get_version_info(version_id)
if version_info:
    print(f"File: {version_info.file_path}")
    print(f"Created: {version_info.timestamp}")
    print(f"Author: {version_info.author}")
    print(f"Reason: {version_info.change_reason}")
```

#### Getting Version Content

```python
# Get the content of a specific version
content = await version_manager.get_version_content(version_id)
if content:
    print(f"Content length: {len(content)}")
    print(f"First 100 chars: {content[:100]}")
```

#### Restoring Versions

```python
# Restore a file to a previous version
success = await version_manager.restore_version(file_path, version_id)
if success:
    print(f"Successfully restored {file_path} to version {version_id}")
else:
    print(f"Failed to restore {file_path} to version {version_id}")
```

#### Bulk Restoration

```python
# Restore multiple files to specific versions at once
restore_map = {
    "/path/to/file1.txt": "version_id_1",
    "/path/to/file2.py": "version_id_2",
}
results = await version_manager.bulk_restore_versions(restore_map)
for file_path, success in results.items():
    print(f"{file_path}: {'Success' if success else 'Failed'}")
```

#### Cleanup of Old Versions

```python
# Clean up versions older than a specified number of days
# If days=None, it uses the configured version_retention_days value
removed_count = await version_manager.cleanup_old_versions(days=30)
print(f"Removed {removed_count} old versions")
```

## Integration with File Watcher

The versioning system is integrated with the `FileEventHandler` to automatically
create versions when files change:

- When files are created, they can be versioned after initial processing
- When files are modified, versions are created if `version_on_modify` is
  enabled
- When files are moved, versions are created in their new location
- When significant changes are detected (major or critical), versions are
  created regardless of other settings

```python
# File watcher integration example
if self.auto_version and self.version_on_modify:
    await version_manager.create_version(
        file_path,
        change_reason="Auto-saved on external modification",
        author="System"
    )
```

## Storage Structure

Versions are stored in a configurable directory structure:

- Base directory: `DATA_DIR / "versions"`
- Shard directories: Files are sharded by hash to avoid too many files in one
  directory
- Version files: Stored with a unique identifier combining file hash and
  timestamp
- Diff files: Stored with a `.diff` extension for diff-based versions

Version metadata is stored in a central JSON file (`version_metadata.json`) with
information about all versions.

## Automatic Cleanup

The system includes a background thread that periodically cleans up old versions
based on the configured retention period. This helps manage disk space usage
over time.

```python
# The cleanup task runs in a background thread
def cleanup_task():
    while True:
        try:
            # Run cleanup
            asyncio.run(version_manager.cleanup_old_versions())

            # Sleep until next cleanup time
            cleanup_interval_hours = config.get("versioning", {}).get("cleanup_interval_hours", 24)
            time.sleep(cleanup_interval_hours * 3600)
        except Exception as e:
            logger.error(f"Error in version cleanup task: {e}")
            # Don't crash the thread, just wait and retry
            time.sleep(3600)  # Wait an hour and try again
```

## Implementation Details

### Diff Generation and Application

For text files, the versioning system uses Python's `difflib` to generate
unified diffs between versions. These diffs are stored and later applied to
reconstruct the full file content when needed.

```python
# Generating a diff
diff = difflib.unified_diff(
    parent_lines,
    current_lines,
    fromfile=f"{file_path}.{parent_version_id}",
    tofile=f"{file_path}.current",
    n=3  # Context lines
)
```

### Version Reconstruction

When retrieving a diff-based version, the system needs to reconstruct the full
content by applying a chain of diffs:

1. Collect all diffs in the chain from the requested version back to the base
   version
2. Start with the base version content (a full copy)
3. Apply each diff in reverse order to reconstruct the requested version

### Singleton Pattern

The `VersionManager` uses a singleton pattern to ensure only one instance exists
throughout the application:

```python
def __new__(cls, *args, **kwargs):
    """Ensure VersionManager is a singleton."""
    if cls._instance is None:
        cls._instance = super(VersionManager, cls).__new__(cls)
    return cls._instance
```

## Best Practices

1. **Configure versioning policies based on file types**: Use the default HYBRID
   policy for most cases, but consider FULL_COPY for small critical files and
   DIFF_BASED for large text files.

2. **Set appropriate retention periods**: Balance the need for history with disk
   space constraints. 30 days is a good default for most uses.

3. **Include only relevant file patterns**: Add only important file types to the
   include_patterns to avoid wasting space.

4. **Monitor disk usage**: Keep an eye on the disk space used by versions,
   especially when working with large files.

5. **Use meaningful change reasons**: When manually creating versions, provide
   descriptive change reasons to make it easier to navigate the version history.

## Example Workflows

### Tracking Document Changes

```python
# Create a version before starting a major edit
await version_manager.create_version(
    Path("/path/to/document.md"),
    change_reason="Before adding new section on API",
    author="John"
)

# ... Make changes to the document ...

# Create another version after completing the edit
await version_manager.create_version(
    Path("/path/to/document.md"),
    change_reason="Added API documentation section",
    author="John"
)
```

### Reverting Unwanted Changes

```python
# List all versions of a file
versions = await version_manager.list_versions(Path("/path/to/code.py"))

# Find the version before the unwanted changes
target_version = None
for version in versions:
    if "before refactoring" in version.change_reason:
        target_version = version.version_id
        break

# Restore to that version if found
if target_version:
    await version_manager.restore_version(Path("/path/to/code.py"), target_version)
```

### Comparing Different Versions

```python
# Get content of two different versions
old_content = await version_manager.get_version_content(old_version_id)
new_content = await version_manager.get_version_content(new_version_id)

# Compare them using difflib
import difflib
diff = difflib.unified_diff(
    old_content.splitlines(),
    new_content.splitlines(),
    fromfile=f"Version {old_version_id}",
    tofile=f"Version {new_version_id}"
)
print("\n".join(diff))
```
