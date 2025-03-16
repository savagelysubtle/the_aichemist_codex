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
  - Chunked file reading and writing
  - Streaming operations for large files
- Example usage:
  ```python
  # Read file
  content = await AsyncFileIO.read(file_path)

  # Write JSON
  success = await AsyncFileIO.write_json(file_path, data)

  # Copy file
  success = await AsyncFileIO.copy(source, destination)

  # Read large file in chunks
  async for chunk in AsyncFileIO.read_chunked(file_path, chunk_size=8192):
      process_chunk(chunk)
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

### 6. Cache Manager (cache_manager.py)

- Efficient caching system
- Features:
  - In-memory LRU cache
  - Disk-based persistent cache
  - Time-to-live (TTL) support
  - Automatic cache invalidation
  - Thread-safe operations
- Example usage:

  ```python
  cache = CacheManager()

  # Store in cache
  await cache.put("key", data, ttl=300)

  # Retrieve from cache
  cached_data = await cache.get("key")

  # Invalidate cache entry
  cache.invalidate("key")

  # Get cache statistics
  stats = cache.get_stats()
  ```

### 7. Batch Processor (batch_processor.py)

- Parallel batch processing
- Features:
  - Concurrent task execution
  - Configurable batch size
  - Error handling for individual items
  - Progress tracking
  - Resource management
- Example usage:

  ```python
  batch_processor = BatchProcessor()

  async def process_item(item):
      # Process single item
      return result

  # Process items in parallel batches
  results = await batch_processor.process_batch(
      items=items_list,
      process_func=process_item,
      batch_size=20
  )
  ```

### 8. Concurrency (concurrency.py)

- Enhanced async threading capabilities
- Features:
  - Task prioritization
  - Rate limiting
  - Task queue management
  - Graceful shutdown
- Example usage:

  ```python
  executor = AsyncThreadPoolExecutor()

  # Submit task with priority
  result = await executor.submit(
      func=process_data,
      args=(data,),
      priority=TaskPriority.HIGH
  )

  # Process batch with rate limiting
  results = await executor.submit_batch(
      items=items_list,
      process_func=process_item,
      max_rate=10  # items per second
  )
  ```

### 9. MIME Type Detector (mime_type_detector.py)

- File type detection based on MIME types
- Features:
  - Automatic file type detection
  - Confidence scoring
  - Fallback mechanisms
  - Custom type handling
- Example usage:

  ```python
  detector = MimeTypeDetector()

  # Get MIME type with confidence score
  mime_type, confidence = detector.get_mime_type(file_path)

  # Use MIME type for content handling
  if mime_type.startswith("text/"):
      # Process as text file
      content = await AsyncFileIO.read(file_path)
  ```

### 10. Utilities (utils.py)

- General utility functions
- Features:
  - Package name canonicalization
  - Version parsing and normalization
  - File listing
  - Text summarization
  - Project management helpers
  - Package filename parsing
- Example usage:

  ```python
  # Canonicalize package name
  normalized = canonicalize_name("My-Package")

  # Parse wheel filename
  name, version, build, tags = parse_wheel_filename("package-1.0-py3-none-any.whl")

  # List Python files
  python_files = list_python_files(directory_path)

  # Summarize text for GPT
  summary = summarize_for_gpt(long_text, max_sentences=10, max_length=1000)
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

### MIME Type Detection

```python
class MimeTypeDetector:
    @staticmethod
    def get_mime_type(file_path: Path) -> tuple[str, float]:
        """Determine the MIME type of a file with confidence score"""
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
- mimetypes for MIME type detection

## Best Practices

- Use async I/O for all file operations
- Implement proper error handling
- Apply safety checks to prevent path traversal
- Leverage caching for repetitive operations
- Use batch processing for large datasets
- Implement rate limiting for external API calls
- Handle MIME types appropriately for content processing

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
