# Search Package Documentation

## Overview
The Search package provides comprehensive search capabilities using multiple search technologies. It implements full-text search with Whoosh, fuzzy matching with RapidFuzz, metadata search with SQLite, semantic search using FAISS and sentence-transformers, and regex pattern matching, all with asynchronous operations support.

## Components

### Search Engine (search_engine.py)
- Core search functionality
- Features:
  - Multiple search types
  - Asynchronous operations
  - Index management
  - Metadata tracking
  - Semantic search
  - Regex search
- Example usage:
  ```python
  search_engine = SearchEngine(index_dir=Path("search_index"))

  # Different search types
  filename_results = await search_engine.search_filename_async("example")
  fuzzy_results = await search_engine.fuzzy_search_async("exmple")
  full_text_results = search_engine.full_text_search("searchable")
  semantic_results = await search_engine.semantic_search_async("document text")
  regex_results = await search_engine.regex_search_async("pattern\d+")
  ```

### Search Providers (providers/)

- Modular search implementation
- Protocol-based interface
- Specialized providers for different search types
- Extensible architecture for adding new search methods
- Example:

  ```python
  @runtime_checkable
  class SearchProvider(Protocol):
      async def search(self, query: str, **kwargs) -> List[str]:
          ...
  ```

## Search Technologies

### 1. Full-Text Search (Whoosh)

- Features:
  - Content indexing
  - Stemming analysis
  - Query parsing
  - Relevance ranking
- Schema:

  ```python
  Schema(
      path=ID(stored=True, unique=True),
      content=TEXT(stored=False, analyzer=StemmingAnalyzer())
  )
  ```

### 2. Fuzzy Search (RapidFuzz)

- Features:
  - Approximate matching
  - Configurable threshold
  - Filename matching
  - Fast performance
- Example:

  ```python
  results = await search_engine.fuzzy_search_async(
      query="example",
      threshold=80.0
  )
  ```

### 3. Metadata Search (SQLite)

- Features:
  - Async operations
  - Multiple filters
  - Tag support
  - Size/date filtering
- Filter options:

  ```python
  filters = {
      "extension": [".txt", ".md"],
      "size_min": 1000,
      "size_max": 5000000,
      "date_after": "2024-01-01",
      "date_before": "2024-12-31",
      "tags": ["important", "document"]
  }
  ```

### 4. Semantic Search (FAISS)

- Features:
  - Vector embeddings
  - Similarity matching
  - Neural language models
  - Scalable indexing
- Components:
  - SentenceTransformer model
  - FAISS index
  - Vector mapping

### 5. Regex Search (RegexSearchProvider)

- Features:
  - Pattern-based content matching
  - Case sensitivity options
  - Whole word matching
  - Streaming file reading
  - Parallel processing
  - Result caching
  - Timeout protection
  - Binary file detection
- Example:

  ```python
  results = await search_engine.regex_search_async(
      pattern=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
      case_sensitive=True,
      whole_word=True
  )
  ```

## Implementation Details

### Database Schema

```sql
CREATE TABLE files (
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE,
    filename TEXT,
    extension TEXT,
    size INTEGER,
    created_at TEXT,
    updated_at TEXT,
    tags TEXT
)
```

### Index Management

- Whoosh index for full-text
- FAISS index for vectors
- SQLite for metadata
- File path mapping

### Search Operations

- Asynchronous I/O
- Thread management
- Error handling
- Result ranking

### Regex Pattern Validation

```python
def _estimate_complexity(self, pattern: str) -> int:
    """
    Estimate the complexity of a regex pattern.

    Args:
        pattern: The regex pattern string

    Returns:
        Complexity score (higher is more complex)
    """
    # Simple heuristic for pattern complexity
    complexity = len(pattern) * 2

    # Penalize potentially expensive operations
    complexity += pattern.count("*") * 10
    complexity += pattern.count("+") * 8
    complexity += pattern.count("{") * 10
    complexity += pattern.count("?") * 5
    complexity += pattern.count("|") * 15
    complexity += pattern.count("[") * 5
    complexity += pattern.count("(") * 8

    # Nested groups are particularly expensive
    depth = 0
    max_depth = 0
    for char in pattern:
        if char == "(":
            depth += 1
            max_depth = max(max_depth, depth)
        elif char == ")":
            depth = max(0, depth - 1)

    complexity += max_depth * 20

    return complexity
```

## Integration Points

### Internal Dependencies

- File Reader for content
- Utils for async I/O
- SQL async for database
- File metadata handling

### External Dependencies

- whoosh: Full-text search
- rapidfuzz: Fuzzy matching
- faiss-cpu: Vector search
- sentence-transformers: Text embeddings

## Best Practices

### Indexing Content

```python
# For synchronous context
search_engine.add_to_index(
    FileMetadata(
        path=file_path,
        mime_type="text/plain",
        size=1024,
        extension=".txt",
        preview="Document content",
        tags=["important"]
    )
)

# In async context, proper await is required
await search_engine.add_to_index_async(
    FileMetadata(
        path=file_path,
        mime_type="text/plain",
        size=1024,
        extension=".txt",
        preview="Document content",
        tags=["important"]
    )
)
```

### Async/Await Best Practices

```python
# Only use await with functions that actually return awaitables
await search_engine.search_filename_async("query")  # Correct - async function

# Don't use await with synchronous functions
results = search_engine.full_text_search("query")  # Correct - sync function

# When testing with pytest.mark.asyncio, ensure proper awaiting
@pytest.mark.asyncio
async def test_async_function():
    # Only await functions that return coroutines
    results = await truly_async_function()

    # Don't await functions that return None or non-coroutines
    non_async_function()  # No await here
```

### Search Operations

```python
# Filename search
results = await search_engine.search_filename_async("document")

# Fuzzy search
results = await search_engine.fuzzy_search_async("docment", threshold=80.0)

# Full-text search
results = search_engine.full_text_search("content keywords")

# Metadata search
results = await search_engine.metadata_search_async({
    "extension": [".txt"],
    "size_min": 1024
})

# Semantic search
results = await search_engine.semantic_search_async("similar content")

# Regex search
results = await search_engine.regex_search_async(r"pattern\d+")
```

### Performance Tips

- Use appropriate search type based on needs
- Limit search scope when possible
- Use `add_to_index` in batch for multiple files
- Implement caching for frequent searches
- Monitor and optimize index size

## Testing

The package includes comprehensive tests:

- test_search_engine.py
  - Tests all search types
  - Verifies correct indexing
  - Tests error handling
  - Ensures proper async/await usage
  - Verifies search result accuracy
- test_providers/*.py
  - Individual provider tests
  - Performance benchmarks
  - Edge case handling

## Known Issues and Fixes

1. **"None" is not awaitable error**:
   - Only use `await` with async functions that return awaitable objects
   - For functions that don't return awaitables, remove the `await` keyword
   - In test contexts, use `# type: ignore` comments when appropriate to handle type checking issues

2. **Async test failures**:
   - Ensure test fixtures properly setup and teardown async resources
   - Use `asyncio.gather` for parallel operations
   - Implement proper cleanup in `finally` blocks

3. **Index corruption recovery**:
   - Automatic index rebuilding on corruption
   - Index versioning and validation

## Future Improvements

### Short-term

1. Enhanced binary file search
2. Improved performance for large directories
3. More sophisticated relevance scoring
4. Better multilingual support
5. Extended regex capabilities

### Long-term

1. Distributed search across multiple nodes
2. Machine learning-based search optimization
3. Real-time indexing improvements
4. Natural language query processing
5. Visual content search integration
