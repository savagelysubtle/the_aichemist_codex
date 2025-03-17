# The Aichemist Codex

<div align="center">
  <img src="docs/images/logo.svg" alt="The Aichemist Codex Logo" width="200" height="200">
</div>

## Intelligent File Management and Knowledge Extraction System

[Key Features](#key-features) • [Installation](#installation) • [Usage](#usage)
• [Architecture](#architecture) • [Documentation](#documentation) •
[Roadmap](#roadmap) • [Contributing](#contributing) • [License](#license)

## Overview

The Aichemist Codex is an advanced file management and knowledge extraction
system designed to transform how you interact with your files and documents. It
leverages AI and machine learning to provide intelligent file organization,
content analysis, and relationship mapping, making it easier to find,
understand, and utilize information across your digital workspace.

## Key Features

### File Management

- **Asynchronous File Operations**: High-performance file I/O with chunked
  processing and streaming support
- **Rule-Based File Organization**: Automatically sort and organize files based
  on customizable rules
- **Rollback System**: Safely undo operations with comprehensive transaction
  management
- **Duplicate Detection**: Identify and manage duplicate files across your
  workspace

### Content Analysis

- **Comprehensive Metadata Extraction**: Extract rich metadata from diverse file
  types
- **MIME Type Detection**: Accurately identify file types for proper handling
- **File Relationship Mapping**: Discover connections between files based on
  content, references, and structure
- **Intelligent Auto-Tagging**: Automatically categorize files using advanced
  NLP techniques

### Search & Retrieval

- **Multi-Modal Search**: Find files using full-text, metadata, fuzzy, or
  semantic search
- **File Similarity Detection**: Identify similar files and content clusters
- **Advanced Filtering**: Filter search results based on tags, metadata,
  relationships, or content

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
import asyncio
from the_aichemist_codex.backend.file_reader import FileReader
from the_aichemist_codex.backend.metadata import MetadataManager
from the_aichemist_codex.backend.search import SearchEngine
from the_aichemist_codex.backend.relationships import RelationshipGraph
from pathlib import Path

async def main():
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
    from the_aichemist_codex.backend.tagging import TagManager, TagSuggester
    tag_manager = TagManager(Path(".aichemist/tags.db"))
    await tag_manager.initialize()
    suggester = TagSuggester(tag_manager)
    suggestions = await suggester.suggest_tags(metadata)

    # Apply high-confidence tags
    high_confidence_tags = [(tag, conf) for tag, conf in suggestions if conf > 0.8]
    if high_confidence_tags:
        await tag_manager.add_file_tags(Path("document.pdf"), high_confidence_tags)

# Run the async function
asyncio.run(main())
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

### Package Structure

The project follows a clean, organized package structure:

```
the_aichemist_codex/
├── backend/
│   ├── config/               # Configuration management
│   ├── file_manager/         # File operations and organization
│   ├── metadata/             # Metadata extraction and management
│   ├── search/               # Search functionality
│   ├── relationships/        # File relationship mapping
│   ├── tagging/              # Auto-tagging capabilities
│   └── utils/                # Utility functions
├── cli/                      # Command-line interface
└── gui/                      # (Future) Graphical user interface
```

All imports should use the full package path:

```python
# Correct import pattern
from the_aichemist_codex.backend.config import settings
from the_aichemist_codex.backend.file_manager import FileManager

# Avoid relative imports across package boundaries
```

## Documentation

Comprehensive documentation is available in the `docs/` directory:

- [Project Summary](docs/project_summary.md)
- [Getting Started Guide](docs/getting_started.rst)
- [Installation Guide](docs/installation.rst)
- [Usage Guide](docs/usage.rst)
- [Configuration Guide](docs/configuration.rst)
- [API Reference](docs/api/)
- [Development Roadmap](docs/roadmap.rst)

## Roadmap

Check out our [Development Roadmap](docs/roadmap.rst) for upcoming features and
improvements.

Current focus areas:

- **Monitoring & Change Tracking**
  - Real-time file tracking
  - File versioning
- **Expanded Format Support**
  - Binary & specialized file support
  - Format conversion capabilities
- **Future Phases**
  - AI-powered enhancements
  - External integrations & API
  - Continuous improvement

## Contributing

Contributions are welcome! Please check our
[Contributing Guidelines](docs/contributing.rst) for details on how to submit
issues, pull requests, and coding standards.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file
for details.

## Acknowledgements

- Built with Python and modern async libraries
- Leverages advanced NLP and ML techniques for intelligent processing
- Special thanks to all contributors

---

<div align="center">
  <p>Made with ❤️ by The Aichemist Team</p>
</div>
