# AIchemist Codex - Search Commands

The AIchemist Codex CLI provides powerful search capabilities to help you find and analyze files in your codebase. This document outlines the available search commands and how to use them.

## Prerequisites

Ensure you have the required dependencies installed:

```bash
pip install faiss-cpu sentence-transformers
```

## Available Commands

### Index Files

Before using search functionality, you need to index your files:

```bash
aichemist search index ./src
```

Options:
- `--recursive/--no-recursive`: Index directories recursively (default: true)
- `--batch-size`, `-b`: Batch size for indexing (default: 20)
- `--index-dir`: Directory for search index (default: ./.aichemist/search_index)

### Search Files

Search for files by name or content:

```bash
aichemist search files "query"
```

Options:
- `--method`, `-m`: Search method (fuzzy, filename, fulltext, semantic) (default: fuzzy)
- `--case-sensitive`, `-c`: Enable case-sensitive search
- `--threshold`, `-t`: Match threshold (0-100) (default: 80.0)
- `--max`, `-n`: Maximum results to show (default: 20)
- `--index-dir`: Directory for search index (default: ./.aichemist/search_index)

Examples:
```bash
# Fuzzy search for filename
aichemist search files config

# Full-text search for content
aichemist search files "import numpy" --method fulltext

# Semantic search for conceptually similar content
aichemist search files "authentication flow" --method semantic
```

### Regex Search

Search for regex patterns in file contents:

```bash
aichemist search regex "pattern"
```

Options:
- `--path`, `-p`: Directory or file to search in (default: .)
- `--case-sensitive`, `-c`: Enable case-sensitive search
- `--whole-word`, `-w`: Match whole words only
- `--max`, `-n`: Maximum results to show (default: 20)
- `--index-dir`: Directory for search index (default: ./.aichemist/search_index)

Examples:
```bash
# Find imports
aichemist search regex "import.*numpy"

# Find class definitions with case sensitivity
aichemist search regex "class\s+\w+" --path ./src --case-sensitive

# Find whole word matches
aichemist search regex "function" --whole-word
```

### Find Similar Files

Find files similar to a given file:

```bash
aichemist search similar path/to/file.py
```

Options:
- `--threshold`, `-t`: Similarity threshold (0.0-1.0) (default: 0.7)
- `--max`, `-n`: Maximum results to show (default: 10)
- `--index-dir`: Directory for search index (default: ./.aichemist/search_index)

Examples:
```bash
# Find files similar to a specific module
aichemist search similar src/main.py

# Adjust similarity threshold
aichemist search similar src/utils/helpers.py --threshold 0.8
```

### Find File Groups

Group similar files together:

```bash
aichemist search groups ./src
```

Options:
- `--threshold`, `-t`: Similarity threshold (0.0-1.0) (default: 0.7)
- `--min-size`, `-m`: Minimum group size (default: 2)
- `--index-dir`: Directory for search index (default: ./.aichemist/search_index)

Examples:
```bash
# Find groups with higher similarity threshold
aichemist search groups ./src --threshold 0.8

# Find larger groups
aichemist search groups ./src --min-size 3
```

## Advanced Usage

### Custom Index Directory

You can specify a custom index directory for all search commands:

```bash
aichemist search index ./src --index-dir ./my-custom-index
aichemist search files "query" --index-dir ./my-custom-index
```

### Using Search Results

The search results display file paths that you can use with other commands:

```bash
# Find files and then check their details
aichemist search files "config"
aichemist fs info path/to/found/file.py
```

## Troubleshooting

### Missing Dependencies

If you see errors about missing dependencies, install them:

```bash
pip install faiss-cpu sentence-transformers rapidfuzz whoosh
```

### Slow Semantic Search

Semantic search requires more processing power. For large codebases:
- Use more specific search paths
- Increase batch size
- Be more specific with queries
