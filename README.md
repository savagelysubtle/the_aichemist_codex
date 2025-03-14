# The Aichemist Codex

A powerful file management and code analysis system with advanced search capabilities, batch processing, and secure configuration management.

## Features

- **Advanced File Management**
  - Asynchronous file operations
  - Batch processing for efficient operations
  - Streaming support for large files
  - Automatic file organization

- **Powerful Search Engine**
  - Full-text search with Whoosh
  - Fuzzy search with RapidFuzz
  - Semantic search with FAISS and sentence-transformers
  - Metadata-based filtering

- **Performance Optimizations**
  - LRU and disk-based caching
  - Asynchronous I/O operations
  - Concurrent processing with priority scheduling
  - Memory-efficient streaming operations

- **Security Features**
  - Encrypted configuration storage
  - Key rotation mechanism
  - Secure file permissions
  - Path validation and sanitization

## Architecture

The Aichemist Codex is organized into several key packages:

- **Backend**: Core functionality
  - **Config**: Configuration management and settings
  - **File Manager**: File operations and organization
  - **Utils**: Utility functions and helpers
  - **Search Engine**: Search and indexing capabilities
  - **Project Reader**: Code analysis and parsing

## Getting Started

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/the_aichemist_codex.git
   cd the_aichemist_codex
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the package in development mode:
   ```bash
   pip install -e .
   ```

### Usage

```python
from backend.file_manager.file_tree import generate_file_tree
from backend.search_engine.search_engine import SearchEngine
from backend.config.secure_config import secure_config

# Generate a file tree
file_tree = await generate_file_tree("/path/to/directory", use_cache=True)

# Initialize search engine
search_engine = SearchEngine()
await search_engine.add_directory("/path/to/directory")

# Search for files
results = await search_engine.search("query")

# Store sensitive configuration
secure_config.set("api_key", "your-secret-api-key")
```

## Development

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific tests
python -m pytest tests/test_secure_config.py
```

### Project Structure

```
the_aichemist_codex/
├── backend/
│   ├── config/           # Configuration management
│   ├── file_manager/     # File operations
│   ├── project_reader/   # Code analysis
│   ├── search_engine/    # Search capabilities
│   ├── utils/            # Utility functions
│   └── output_formatter/ # Output formatting
├── data/                 # Data storage
├── tests/                # Test suite
├── pyproject.toml        # Project configuration and dependencies
└── architecture_docs/    # Documentation
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- The project uses several open-source libraries and tools
- Special thanks to all contributors

```

