Here's the updated content for modules/search.md:

```markdown
# Search Package Documentation

## Overview
The Search package provides comprehensive search capabilities using multiple search technologies. It implements full-text search with Whoosh, fuzzy matching with RapidFuzz, metadata search with SQLite, and semantic search using FAISS and sentence-transformers, all with asynchronous operations support.

## Components

### Search Engine (search_engine.py)
- Core search functionality
- Features:
  - Multiple search types
  - Asynchronous operations
  - Index management
  - Metadata tracking
  - Semantic search
- Example usage:
  ```python
  search_engine = SearchEngine(index_dir=Path("search_index"))
  
  # Different search types
  filename_results = await search_engine.search_filename_async("example")
  fuzzy_results = await search_engine.fuzzy_search_async("exmple")
  full_text_results = search_engine.full_text_search("searchable")
  semantic_results = await search_engine.semantic_search_async("document text")
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

```

This documentation accurately reflects the current implementation while providing clear examples and usage patterns. It covers all major components and their interactions, making it easier for developers to understand and use the search system effectively.

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
