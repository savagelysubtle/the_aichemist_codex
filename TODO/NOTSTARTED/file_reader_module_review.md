# File Reader Module Review and Improvement Plan

## Table of Contents

1. [Current Implementation](#current-implementation)
2. [Architectural Compliance](#architectural-compliance)
3. [Areas for Improvement](#areas-for-improvement)
4. [Recommendations](#recommendations)
5. [Implementation Plan](#implementation-plan)
6. [Priority Matrix](#priority-matrix)

## Current Implementation

The file_reader module is responsible for low-level file access and basic file
operations. The key components include:

- **FileReaderImpl**: Main implementation of the FileReader interface
- **Parsers**: Specialized parsers for different file formats
- Key functionalities:
  - Reading and parsing different file formats (text, binary, JSON, YAML)
  - Extracting basic file metadata
  - Determining MIME types
  - Generating content previews

## Architectural Compliance

The file_reader module demonstrates good alignment with the project's
architectural guidelines:

| Architectural Principle    | Status | Notes                                                                            |
| -------------------------- | :----: | -------------------------------------------------------------------------------- |
| **Layered Architecture**   |   ✅   | Properly positioned in the infrastructure/utility layer                          |
| **Registry Pattern**       |   ✅   | Uses Registry for dependency injection and service access                        |
| **Interface-Based Design** |   ✅   | FileReaderImpl properly implements the FileReader interface                      |
| **Import Strategy**        |   ✅   | Uses absolute imports for core interfaces and relative imports for local modules |
| **Asynchronous Design**    |   ✅   | Methods consistently use async/await patterns                                    |
| **Error Handling**         |   ✅   | Uses specific FileReaderError with context                                       |

## Areas for Improvement

Despite good architectural alignment, several areas need improvement:

| Area                     | Status | Issue                                              |
| ------------------------ | :----: | -------------------------------------------------- |
| **Format Extension**     |   🔄   | Limited support for specialized file formats       |
| **Streaming Support**    |   ⚠️   | Lacks efficient streaming for large files          |
| **Caching**              |   ❌   | No caching mechanism for frequently accessed files |
| **Parser Extensibility** |   🔄   | Parser system could be more extensible             |
| **Metadata Enrichment**  |   ⚠️   | Basic metadata extraction can be enhanced          |
| **Error Recovery**       |   ⚠️   | Limited recovery strategies for file read failures |
| **Charset Detection**    |   ⚠️   | Relies on default encoding without auto-detection  |

## Recommendations

### 1. Enhance Format Support with Plugin System

- Create a plugin system for file format parsers
- Allow registration of custom parsers at runtime

```python
# domain/file_reader/parser_registry.py
class ParserRegistry:
    """Registry for file format parsers."""

    def __init__(self):
        self._parsers = {}
        self._mime_type_mappings = {}

    def register_parser(self, parser_cls, mime_types=None, extensions=None):
        """Register a parser for specific MIME types and extensions."""
        parser_name = parser_cls.__name__
        self._parsers[parser_name] = parser_cls

        # Register MIME type mappings
        if mime_types:
            for mime_type in mime_types:
                self._mime_type_mappings[mime_type] = parser_name

        # Register extension mappings
        if extensions:
            for ext in extensions:
                mime_type = mimetypes.guess_type(f"file.{ext}")[0]
                if mime_type:
                    self._mime_type_mappings[mime_type] = parser_name

    def get_parser_for_mime_type(self, mime_type):
        """Get the appropriate parser for a MIME type."""
        parser_name = self._mime_type_mappings.get(mime_type)
        if parser_name:
            return self._parsers[parser_name]
        return None
```

### 2. Implement Efficient Streaming Support

- Add streaming support for large files
- Use generators and async iterators

```python
# domain/file_reader/file_reader.py
class FileReaderImpl(FileReaderInterface):
    # ... existing implementation ...

    async def stream_text(self, file_path: str, chunk_size: int = 4096):
        """
        Stream a text file in chunks.

        Args:
            file_path: Path to the file
            chunk_size: Size of each chunk in bytes

        Yields:
            Text chunks from the file
        """
        validated_path = self._validator.ensure_path_safe(file_path)

        try:
            async for chunk in self._async_io.stream_file(validated_path, chunk_size):
                yield chunk.decode('utf-8', errors='replace')
        except Exception as e:
            raise FileReaderError(f"Failed to stream file: {e}", file_path=file_path)

    async def stream_binary(self, file_path: str, chunk_size: int = 4096):
        """
        Stream a binary file in chunks.

        Args:
            file_path: Path to the file
            chunk_size: Size of each chunk in bytes

        Yields:
            Binary chunks from the file
        """
        validated_path = self._validator.ensure_path_safe(file_path)

        try:
            async for chunk in self._async_io.stream_file(validated_path, chunk_size):
                yield chunk
        except Exception as e:
            raise FileReaderError(f"Failed to stream binary file: {e}", file_path=file_path)
```

### 3. Add File Caching Mechanism

- Implement caching for frequently accessed files
- Use LRU cache strategy with TTL

```python
# infrastructure/cache/file_cache.py
class FileCache:
    """Cache for file contents with LRU eviction strategy."""

    def __init__(self, max_size_mb=100, ttl_seconds=300):
        self._max_size = max_size_mb * 1024 * 1024  # Convert to bytes
        self._ttl = ttl_seconds
        self._cache = {}
        self._access_times = {}
        self._size = 0

    async def get(self, file_path: str, last_modified_time: float = None):
        """
        Get cached file content if available and not expired.

        Args:
            file_path: Path to the file
            last_modified_time: Last modification time of the file

        Returns:
            Cached content or None if not available
        """
        key = self._get_cache_key(file_path)

        if key not in self._cache:
            return None

        # Check if content is expired
        now = time.time()
        if now - self._access_times[key]["added"] > self._ttl:
            self._remove_item(key)
            return None

        # Check if file has been modified since caching
        if (last_modified_time and
            last_modified_time > self._access_times[key]["added"]):
            self._remove_item(key)
            return None

        # Update access time
        self._access_times[key]["last_accessed"] = now

        return self._cache[key]

    async def put(self, file_path: str, content):
        """
        Cache file content.

        Args:
            file_path: Path to the file
            content: Content to cache
        """
        key = self._get_cache_key(file_path)
        content_size = sys.getsizeof(content)

        # Check if we need to make room
        if self._size + content_size > self._max_size:
            self._evict_lru_until_fits(content_size)

        # Store in cache
        self._cache[key] = content
        now = time.time()
        self._access_times[key] = {
            "added": now,
            "last_accessed": now
        }
        self._size += content_size

    # ... helper methods for eviction, cache key generation, etc.
```

### 4. Improve Character Encoding Detection

- Implement smart character encoding detection
- Support different encodings based on file type and content

```python
# domain/file_reader/encoding_detector.py
class EncodingDetector:
    """Detector for file character encodings."""

    def __init__(self):
        # Common encodings to try in order
        self._encodings = [
            'utf-8', 'utf-16', 'utf-32',
            'latin-1', 'iso-8859-1', 'ascii'
        ]

    async def detect_encoding(self, file_path: str, read_bytes: int = 4096):
        """
        Detect character encoding of a file.

        Args:
            file_path: Path to the file
            read_bytes: Number of bytes to read for detection

        Returns:
            Detected encoding name
        """
        try:
            # Try to use chardet if available
            import chardet
            with open(file_path, 'rb') as f:
                sample = f.read(read_bytes)
                result = chardet.detect(sample)
                if result['confidence'] > 0.7:
                    return result['encoding']
        except ImportError:
            pass

        # Fall back to manual detection
        for encoding in self._encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read(read_bytes)
                return encoding
            except UnicodeDecodeError:
                continue

        # Default to UTF-8 if nothing else works
        return 'utf-8'
```

### 5. Enhanced Metadata Extraction

- Extract more comprehensive file metadata
- Support specialized metadata for different file types

```python
# domain/file_reader/metadata_extractor.py
class MetadataExtractor:
    """Extractor for enhanced file metadata."""

    def __init__(self, registry):
        self._registry = registry
        self._extractors = {}
        self._register_default_extractors()

    def _register_default_extractors(self):
        """Register default metadata extractors."""
        self._extractors = {
            'text/plain': PlainTextMetadataExtractor(),
            'application/json': JsonMetadataExtractor(),
            'application/pdf': PdfMetadataExtractor(),
            'image/': ImageMetadataExtractor(),
            'audio/': AudioMetadataExtractor(),
            'video/': VideoMetadataExtractor(),
        }

    async def extract_metadata(self, file_path: str, mime_type: str = None):
        """
        Extract comprehensive metadata for a file.

        Args:
            file_path: Path to the file
            mime_type: Optional MIME type hint

        Returns:
            Dictionary of metadata
        """
        # Get basic file stats
        path = Path(file_path)
        stats = path.stat()

        base_metadata = {
            "filename": path.name,
            "path": str(path.absolute()),
            "size_bytes": stats.st_size,
            "created": datetime.fromtimestamp(stats.st_ctime),
            "modified": datetime.fromtimestamp(stats.st_mtime),
            "accessed": datetime.fromtimestamp(stats.st_atime),
        }

        # Determine MIME type if not provided
        if not mime_type:
            mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'

        base_metadata["mime_type"] = mime_type

        # Find appropriate extractor
        extractor = None
        for key, ext in self._extractors.items():
            if mime_type.startswith(key):
                extractor = ext
                break

        # Extract specialized metadata if possible
        if extractor:
            specialized_metadata = await extractor.extract(file_path, mime_type)
            base_metadata.update(specialized_metadata)

        return base_metadata
```

### 6. Implement Resilient File Reading

- Add retry mechanism for transient file access failures
- Provide recovery strategies for corrupted files

```python
# domain/file_reader/resilient_reader.py
class ResilientReader:
    """Reader with resilience mechanisms for file access issues."""

    def __init__(self, max_retries=3, retry_delay=0.5):
        self._max_retries = max_retries
        self._retry_delay = retry_delay

    async def read_with_retry(self, read_func, *args, **kwargs):
        """
        Execute a read function with retries on failure.

        Args:
            read_func: Async function to execute
            *args, **kwargs: Arguments to pass to read_func

        Returns:
            Result of the read function
        """
        attempts = 0
        last_error = None

        while attempts < self._max_retries:
            try:
                return await read_func(*args, **kwargs)
            except (OSError, IOError) as e:
                # Only retry on specific errors that might be transient
                if e.errno in (5, 13, 16, 17):  # I/O errors, permission errors, etc.
                    attempts += 1
                    last_error = e
                    await asyncio.sleep(self._retry_delay * attempts)
                else:
                    # Non-retriable error
                    raise

        # Max retries reached
        raise FileReaderError(
            f"Failed after {self._max_retries} attempts: {last_error}",
            operation="read_with_retry"
        )

    async def read_with_fallback(self, primary_func, fallback_func, *args, **kwargs):
        """
        Try to read using primary function, fall back to secondary on failure.

        Args:
            primary_func: Primary async read function
            fallback_func: Fallback async read function
            *args, **kwargs: Arguments to pass to read functions

        Returns:
            Result of primary or fallback function
        """
        try:
            return await primary_func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Primary reading method failed: {e}, trying fallback")
            return await fallback_func(*args, **kwargs)
```

## Implementation Plan

### Phase 1: Core Improvements (2 weeks)

1. Implement plugin system for parsers
2. Add streaming support for large files
3. Improve character encoding detection

### Phase 2: Reliability & Performance (2 weeks)

1. Implement file caching mechanism
2. Add resilient reading with retry logic
3. Optimize performance for large files

### Phase 3: Metadata & Specialized Formats (3 weeks)

1. Enhance metadata extraction
2. Add support for more file formats
3. Implement specialized parsers for common formats

### Phase 4: Integration & Testing (1 week)

1. Integrate with other modules
2. Add comprehensive tests
3. Optimize based on performance metrics

## Priority Matrix

| Improvement          | Impact | Effort | Priority |
| -------------------- | :----: | :----: | :------: |
| Streaming Support    |  High  | Medium |    1     |
| File Caching         |  High  | Medium |    2     |
| Parser Plugin System | Medium |  High  |    3     |
| Encoding Detection   | Medium |  Low   |    4     |
| Enhanced Metadata    | Medium | Medium |    5     |
| Resilient Reading    | Medium |  Low   |    6     |
| Specialized Formats  |  Low   |  High  |    7     |
