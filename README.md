# The Aichemist Codex

<div align="center">
  <img src="docs/images/logo.png" alt="The Aichemist Codex Logo" width="200" height="200" style="max-width: 100%;">
  <br>
  <em>Intelligent File Management and Knowledge Extraction System</em>
</div>

<p align="center">
  <a href="#key-features">Key Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#documentation">Documentation</a> •
  <a href="#roadmap">Roadmap</a> •
  <a href="#contributing">Contributing</a> •
  <a href="#license">License</a>
</p>

## Overview

The Aichemist Codex is an advanced file management and knowledge extraction system designed to transform how you interact with your files and documents. It leverages AI and machine learning to provide intelligent file organization, content analysis, and relationship mapping, making it easier to find, understand, and utilize information across your digital workspace.

## Key Features

### File Management
- **Asynchronous File Operations**: High-performance file I/O with chunked processing and streaming support
- **Rule-Based File Organization**: Automatically sort and organize files based on customizable rules
- **Rollback System**: Safely undo operations with comprehensive transaction management
- **Duplicate Detection**: Identify and manage duplicate files across your workspace

### Content Analysis
- **Comprehensive Metadata Extraction**: Extract rich metadata from diverse file types
- **MIME Type Detection**: Accurately identify file types for proper handling
- **File Relationship Mapping**: Discover connections between files based on content, references, and structure
- **Intelligent Auto-Tagging**: Automatically categorize files using advanced NLP techniques

### Search & Retrieval
- **Multi-Modal Search**: Find files using full-text, metadata, fuzzy, or semantic search
- **File Similarity Detection**: Identify similar files and content clusters
- **Advanced Filtering**: Filter search results based on tags, metadata, relationships, or content

### Performance & Security
- **Cache Management**: Efficient caching system with LRU and TTL support
- **Batch Processing**: Parallel operations for handling large datasets
- **Secure Configuration**: Encrypted storage for sensitive configuration values

## Installation

### Prerequisites
- Python 3.10+
- pip or Poetry

### Using pip
```bash
# Clone the repository
git clone https://github.com/yourusername/the_aichemist_codex.git
cd the_aichemist_codex

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .
```

### Using Poetry
```bash
# Clone the repository
git clone https://github.com/yourusername/the_aichemist_codex.git
cd the_aichemist_codex

# Install dependencies
poetry install
```

## Usage

### Command Line Interface

The Aichemist Codex provides a comprehensive CLI for all operations:

```bash
# Initialize a new codex directory
aichemist init /path/to/codex

# Add files or directories to the codex
aichemist add /path/to/files

# Search for content across your codex
aichemist search "query terms"

# Find similar files
aichemist similar /path/to/reference/file.txt

# Generate a relationship map
aichemist relationships /path/to/directory

# Extract and view file metadata
aichemist metadata /path/to/file.txt

# Tag files automatically
aichemist tag --auto /path/to/files

# Organize files based on rules
aichemist organize /path/to/directory
```

### Python API

The Aichemist Codex can also be used as a library in your Python projects:

```python
from backend.src.file_reader import FileReader
from backend.src.metadata import MetadataManager
from backend.src.search import SearchEngine
from backend.src.relationships import RelationshipGraph
from pathlib import Path

# Process files
reader = FileReader()
metadata = await reader.process_file(Path("document.pdf"))

# Search for content
search = SearchEngine()
results = await search.search("machine learning", max_results=10)

# Find relationships
graph = RelationshipGraph()
related_files = await graph.find_related(Path("project.py"))

# Auto-tag files
from backend.src.tagging import AutoTagger
tagger = AutoTagger()
tags = await tagger.generate_tags(Path("article.md"))
```

## Architecture

The Aichemist Codex follows a modular architecture with these core components:

- **File Reader**: Handles file reading and MIME type detection
- **File Manager**: Manages file operations and organization
- **Metadata Manager**: Extracts and stores file metadata
- **Search Engine**: Provides multi-modal search capabilities
- **Relationship Manager**: Maps connections between files
- **Tagging System**: Implements intelligent auto-tagging
- **Rollback System**: Enables safe operations with undo capability

## Documentation

Comprehensive documentation is available in the `docs/` directory:

- [Getting Started Guide](docs/getting_started.md)
- [Architecture Overview](docs/architecture.md)
- [API Reference](docs/api_reference.md)
- [CLI Commands](docs/cli_commands.md)
- [Configuration Guide](docs/configuration.md)

## Roadmap

Check out our [Development Roadmap](docs/roadmap/checklist) for upcoming features and improvements.

Current focus areas:
- Monitoring & Change Tracking
- Expanded Format Support
- AI-Powered Enhancements

## Contributing

Contributions are welcome! Please check our [Contributing Guidelines](CONTRIBUTING.md) for details on how to submit issues, pull requests, and coding standards.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- Built with Python and modern async libraries
- Leverages advanced NLP and ML techniques for intelligent processing
- Special thanks to all contributors

---

<div align="center">
  <p>Made with ❤️ by The Aichemist Team</p>
</div>