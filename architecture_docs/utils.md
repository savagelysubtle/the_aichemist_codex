Here's the updated content for modules/utils.md:

```markdown
# Utils Package Documentation

## Overview
The Utils package provides essential utilities and helper functions used throughout The Aichemist Codex. It implements asynchronous I/O operations, safety checks, error handling, pattern matching, and SQL operations with a focus on performance and security.

## Components

### 1. Async I/O (async_io.py)
- Asynchronous file operations
- Features:
  - Text and binary file handling
  - JSON operations
  - File copying
  - Directory management
  - Error handling
- Example usage:
  ```python
  # Read file
  content = await AsyncFileIO.read(file_path)
  
  # Write JSON
  success = await AsyncFileIO.write_json(file_path, data)
  
  # Copy file
  success = await AsyncFileIO.copy(source, destination)
  ```

### 2. Safety Handler (safety.py)

- File operation safety checks
- Features:
  - Path validation
  - Ignore pattern checking
  - Binary file detection
  - Directory traversal protection
- Example usage:

  ```python
  # Check path safety
  is_safe = SafeFileHandler.is_safe_path(target, base)
  
  # Check ignore patterns
  should_skip = SafeFileHandler.should_ignore(file_path)
  
  # Check binary file
  is_binary = SafeFileHandler.is_binary_file(file_path)
  ```

### 3. Error Handling (errors.py)

- Custom exception classes
- Hierarchy:
  - CodexError (base)
  - MaxTokenError
  - NotebookProcessingError
  - InvalidVersion
- Example usage:

  ```python
  try:
      if tokens > max_tokens:
          raise MaxTokenError(file_path, max_tokens)
  except CodexError as e:
      logger.error(f"Operation failed: {e}")
  ```

### 4. Pattern Matching (patterns.py)

- File pattern management
- Features:
  - Dynamic pattern addition
  - Path normalization
  - Pattern matching
  - Configuration integration
- Example usage:

  ```python
  matcher = PatternMatcher()
  matcher.add_patterns({".git", "__pycache__"})
  should_ignore = matcher.should_ignore(path)
  ```

### 5. Async SQL (sqlasync_io.py)

- Asynchronous SQLite operations
- Features:
  - Query execution
  - Result fetching
  - Batch operations
  - Transaction support
- Example usage:

  ```python
  db = AsyncSQL(db_path)
  
  # Execute query
  await db.execute(query, params, commit=True)
  
  # Fetch results
  rows = await db.fetchall(query, params)
  ```

## Implementation Details

### Async File Operations

```python
class AsyncFileIO:
    @staticmethod
    async def read(file_path: Path) -> str:
        """Async file reading with error handling"""

    @staticmethod
    async def write(file_path: Path, content: str) -> bool:
        """Async file writing with directory creation"""

    @staticmethod
    async def copy(source: Path, destination: Path) -> bool:
        """Async file copying with validation"""
```

### Safety Checks

```python
class SafeFileHandler:
    @staticmethod
    def is_safe_path(target: Path, base: Path) -> bool:
        """Path traversal protection"""

    @staticmethod
    def should_ignore(file_path: Path) -> bool:
        """Pattern-based ignore checking"""
```

### SQL Operations

```python
class AsyncSQL:
    async def execute(self, query: str, params: Tuple = ()) -> None:
        """Async query execution"""

    async def fetchall(self, query: str) -> List[Tuple[Any, ...]]:
        """Async result fetching"""
```

## Integration Points

### Internal Dependencies

- Config package for settings
- Logger for error tracking
- Path handling for files

### External Dependencies

- aiofiles for async I/O
- aiosqlite for async SQL
- fnmatch for patterns

## Best Practices

### File Operations

```python
# Safe file reading
if not SafeFileHandler.should_ignore(path):
    content = await AsyncFileIO.read(path)

# Safe file writing
success = await AsyncFileIO.write(path, content)
```

### Pattern Management

```python
# Add custom patterns
pattern_matcher.add_patterns({
    "*.pyc",
    "__pycache__",
    ".git"
})

# Check patterns
if not pattern_matcher.should_ignore(path):
    # Process file
```

### Error Handling

```python
try:
    await AsyncFileIO.write(path, content)
except Exception as e:
    logger.error(f"Write failed: {e}")
    # Implement recovery strategy
```

## Future Improvements

### Short-term

1. Enhanced error recovery
2. Improved pattern matching
3. Better transaction handling
4. Extended safety checks
5. Performance optimization

### Long-term

1. Distributed file operations
2. Advanced caching
3. Pattern learning
4. Cloud storage support
5. Enhanced monitoring

```

This documentation accurately reflects the current implementation while providing clear examples and usage patterns. It covers all major components and their interactions, making it easier for developers to understand and use the utilities effectively.
