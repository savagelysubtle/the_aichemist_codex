# File Similarity Detection

## Overview

The File Similarity Detection feature enables powerful content-based analysis to identify related files in your collection. Using vector-based embeddings generated from file content, this feature can find files with similar content, themes, or code structures, regardless of naming conventions.

## Key Features

- **Vector-Based Similarity**: Uses TF-IDF embeddings to generate numerical representations of file content, enabling precise mathematical comparison between files.
- **File-to-File Comparison**: Find files similar to a specific reference file.
- **Text-to-File Search**: Search for files similar to a text query.
- **Similar File Grouping**: Automatically cluster related files into meaningful groups.
- **Caching Support**: Results are cached for improved performance on repeated searches.
- **High Performance**: Uses batch processing and parallel file analysis for efficient operation.

## Use Cases

- **Code Repository Analysis**: Identify duplicated or similar code files across projects.
- **Document Organization**: Group related documents together, even if their filenames differ.
- **Content Deduplication**: Find near-duplicate files that contain similar content with minor differences.
- **Research Collections**: Discover thematically related research papers or documents.
- **Project Structure Analysis**: Understand relationships between files in a complex project.

## CLI Commands

### Find Files Similar to a Reference File

```bash
codex similarity find <file> [directory] [--threshold=0.7] [--max-results=20] [--output=results.json]
```

- `<file>`: The reference file to compare against.
- `[directory]`: Optional directory to search within (defaults to current directory).
- `--threshold`: Minimum similarity score (0.0-1.0) for matches (default: 0.7).
- `--max-results`: Maximum number of similar files to return (default: 20).
- `--output`: Optional path to save results as JSON.

### Find Groups of Similar Files

```bash
codex similarity groups <directory> [--threshold=0.7] [--min-group-size=2] [--output=groups.json]
```

- `<directory>`: The directory to analyze.
- `--threshold`: Similarity threshold for group membership (default: 0.7).
- `--min-group-size`: Minimum number of files required to form a group (default: 2).
- `--output`: Optional path to save results as JSON.

## Technical Implementation

The implementation consists of several key components:

### TextEmbeddingModel

Generates vector representations of text content using TF-IDF vectorization, which captures the importance of terms in documents relative to a corpus.

### VectorIndex

Stores and indexes vector embeddings for efficient similarity search, enabling fast retrieval of the most similar vectors to a query vector.

### SimilarityProvider

Orchestrates the similarity search process, including:

- Text query to file search
- File to file similarity comparison
- Hierarchical clustering for file grouping
- Caching of results for performance

### Integration with SearchEngine

The feature is integrated into the main SearchEngine, allowing for seamless access to similarity features alongside existing search capabilities.

## Configuration Options

The following settings can be configured in `settings.py`:

```python
# Similarity Search Settings
SIMILARITY_THRESHOLD = 0.7         # Default threshold for matches (0.0-1.0)
SIMILARITY_MAX_RESULTS = 100       # Maximum results to return
SIMILARITY_CACHE_TTL = 300         # Cache time-to-live in seconds (5 minutes)
SIMILARITY_MIN_GROUP_SIZE = 2      # Minimum size for a group of similar files
SIMILARITY_GROUP_THRESHOLD = 0.6   # Threshold for group membership
```

## Performance Considerations

- **Large Files**: Files over 1MB are skipped during processing to avoid performance issues.
- **Batch Processing**: Files are processed in batches to manage memory usage.
- **Caching**: Results are cached to improve performance on repeated queries.
- **Parallel Processing**: File analysis is performed in parallel for improved speed.

## Future Enhancements

- Deep learning models for more accurate semantic matching
- Support for image and binary file similarity
- Interactive visualization of file relationships
- Improved clustering algorithms for more accurate grouping
- Integration with other features like auto-tagging and organization
