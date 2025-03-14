Here's the updated content for modules/search.md:

```markdown
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
    "tags": ["important"]
})

# Semantic search
results = await search_engine.semantic_search_async(
    "conceptually similar content",
    top_k=5
)
```

### Error Handling

```python
try:
    results = await search_engine.semantic_search_async(query)
    if not results:
        logger.warning("No semantic search results found")
except Exception as e:
    logger.error(f"Search error: {e}")
```

## Future Improvements

### Short-term

1. Enhanced ranking algorithms
2. Better error recovery
3. Improved indexing speed
4. Extended metadata support
5. More search filters

### Long-term

1. Distributed search capabilities
2. Advanced semantic models
3. Real-time indexing
4. Caching system
5. Plugin architecture

## Regex Search Provider

The regex search provider enables powerful pattern matching within file contents using regular expressions. It includes the following features:

- **Pattern Validation**: Validates regex patterns to prevent catastrophic backtracking
- **Streaming File Reading**: Processes large files efficiently by reading in chunks
- **Parallel Processing**: Searches multiple files concurrently for better performance
- **Caching**: Caches search results to improve performance for repeated searches
- **Case Sensitivity**: Supports both case-sensitive and case-insensitive searches
- **Whole Word Matching**: Option to match only whole words rather than substrings
- **Binary File Handling**: Automatically skips binary files to avoid errors
- **Timeout Protection**: Implements timeouts to prevent hanging on complex patterns

### Configuration

Regex search behavior can be configured through settings:

```python
# In backend/config/settings.py
REGEX_MAX_COMPLEXITY = 1000  # Maximum complexity score for regex patterns
REGEX_TIMEOUT_MS = 500       # Timeout for regex search operations in milliseconds
REGEX_CACHE_TTL = 300        # Cache TTL for regex search results (5 minutes)
REGEX_MAX_RESULTS = 100      # Maximum number of results to return
```

## CLI Usage

The search functionality is also available through the command-line interface:

```bash
# Basic search
python -m backend.cli search /path/to/directory "query" --method fulltext

# Regex search
python -m backend.cli search /path/to/directory "pattern\d+" --method regex --case-sensitive --whole-word

# Save results to file
python -m backend.cli search /path/to/directory "query" --method fuzzy --output results.json
```

## Future Roadmap

### Phase 2: Advanced Features
- Enhanced semantic search
- Regex pattern support
- File similarity detection
- Advanced metadata extraction

### Phase 3: AI Capabilities
- ML-based search ranking
- Context-aware search
- Smart recommendations
- Content classification

### Phase 4: Scalability
- Distributed search
- Load balancing
- Sharding support
