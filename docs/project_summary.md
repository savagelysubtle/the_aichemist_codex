# The Aichemist Codex: Project Summary

## What Is The Aichemist Codex?

The Aichemist Codex is an advanced file management and knowledge extraction
system designed to transform how you interact with your files and documents. It
leverages AI and machine learning to provide:

- Intelligent file organization based on content
- Content analysis and metadata extraction
- Relationship mapping between files
- Advanced search capabilities
- Automatic tagging based on file content

## System Requirements

- **Operating System**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+,
  Fedora 34+)
- **Python**: Version 3.10 or higher
- **Disk Space**: At least 100MB for base installation, plus space for your
  files
- **RAM**: 4GB minimum, 8GB recommended

## Installation Methods

### Using pip (Recommended)

```bash
pip install the-aichemist-codex
```

### For Development

```bash
git clone https://github.com/yourusername/the_aichemist_codex.git
cd the_aichemist_codex
pip install -e .
```

### Using Poetry

```bash
# For using as a dependency in your project
poetry add the-aichemist-codex

# For development
git clone https://github.com/yourusername/the_aichemist_codex.git
cd the_aichemist_codex
poetry install
```

### Docker Installation

```bash
docker pull aichemist/codex:latest
docker run -v /path/to/your/files:/data aichemist/codex
```

## Quick Start Guide

1. **Initialize a new codex**

   ```bash
   aichemist init /path/to/your/codex
   ```

2. **Add files to your codex**

   ```bash
   aichemist add /path/to/your/files
   ```

3. **Get tag suggestions**

   ```bash
   aichemist tag --suggest /path/to/your/files
   ```

4. **Apply tags automatically**

   ```bash
   aichemist tag --auto /path/to/your/files
   ```

5. **Search for content**
   ```bash
   aichemist search "your search query"
   ```

## Main Features

### File Management

- **Add Files**: Process and index files for search and organization
- **Organize Files**: Automatically organize files based on configurable rules
- **Find Duplicates**: Identify duplicate files and provide handling options

### Tagging System

- **Auto-Tagging**: Automatically generate and apply tags based on file content
- **Tag Suggestions**: Generate tag suggestions for review before applying
- **Manual Tagging**: Add or remove tags manually
- **Tag Management**: List, filter, and manage tags across your files

### Search Capabilities

- **Basic Search**: Search across all indexed files
- **Fuzzy Search**: Find approximate matches for search terms
- **Semantic Search**: Find conceptually similar content
- **Regex Search**: Use pattern matching with regular expressions
- **Filtered Search**: Search by file type, tag, date, etc.

### Relationship Mapping

- **Detect Relationships**: Analyze files to find connections between them
- **Find Related Files**: Discover files related to a specific file
- **Generate Relationship Maps**: Create visual graphs of file relationships

## Configuration

The Aichemist Codex can be configured via:

1. **YAML Configuration File**: Located at `~/.aichemist/config.yaml` by default
2. **Environment Variables**: Override file settings as needed
3. **Programmatic Configuration**: When using as a library in Python

### Data Directory Structure

The data directory contains the following subdirectories:

```
data/
├── backup/             # File backups for rollback operations
├── cache/              # Temporary cache files
├── exports/            # Exported analysis results
├── logs/               # Application logs
├── notifications/      # Stored notifications
├── trash/              # Deleted files (temporary storage)
└── versions/           # Version history
```

## Using as a Python Library

The Aichemist Codex can be integrated into your Python applications:

```python
import asyncio
from backend.src.file_reader import FileReader
from backend.src.metadata import MetadataManager
from backend.src.search import SearchEngine
from backend.src.tagging import TagManager, TagSuggester
from pathlib import Path

async def main():
    # Initialize components
    reader = FileReader()
    metadata_mgr = MetadataManager()
    search = SearchEngine()
    tag_manager = TagManager(Path(".aichemist/tags.db"))
    await tag_manager.initialize()
    suggester = TagSuggester(tag_manager)

    # Process a file
    file_path = Path("document.pdf")
    metadata = await reader.process_file(file_path)

    # Store metadata
    await metadata_mgr.add(metadata)

    # Get tag suggestions
    tag_suggestions = await suggester.suggest_tags(metadata)

    # Apply high-confidence tags automatically
    high_confidence_tags = [(tag, conf) for tag, conf in tag_suggestions if conf > 0.8]
    if high_confidence_tags:
        await tag_manager.add_file_tags(file_path, high_confidence_tags)

    # Search for content
    results = await search.search("important concept")

    # Print results
    for result in results:
        print(f"Found in: {result.path} (Score: {result.score})")

# Run the async function
asyncio.run(main())
```

## Development Roadmap

The Aichemist Codex follows a phased development approach:

### Phase 1: Core Improvements (Completed ✅)

- **File I/O Standardization & Optimization**

  - Refactored file operations to use `AsyncFileReader` across all components
  - Enhanced `async_io.py` for centralized file operations

- **Rollback Manager & System**

  - Implemented rollback tracking in directory and file operations
  - Added rollback logging and failure recovery

- **File Management & Organization**

  - Rule-based sorting with user-defined rules
  - Duplicate detection using hash-based comparison
  - Auto-folder structuring by type and creation date
  - Event-driven sorting with file watcher

- **Search & Retrieval Enhancements**

  - Full-text search implementation with Whoosh
  - Metadata-based search filtering
  - Fuzzy search via RapidFuzz
  - Semantic search with FAISS and sentence-transformers

- **Performance & Scalability**

  - Batch processing for efficient parallel operations
  - Metadata caching with LRU and disk caching
  - Memory optimization with chunked file operations
  - Concurrency optimization with async processing

- **Security & Compliance**
  - Configuration security with Fernet encryption
  - Secure file permissions and path validation
  - Audit logging for configuration changes

### Phase 2: Feature Enhancements (Current Focus 🎯)

- **Advanced Search & Content Analysis** (Completed ✅)

  - Semantic search with AI-powered retrieval
  - Regex search with pattern matching
  - File similarity detection with vector-based embeddings
  - Enhanced metadata extraction for multiple file types

- **Smart File Organization** (Completed ✅)

  - Intelligent auto-tagging with NLP-based classification
  - Hierarchical tag taxonomies based on content
  - File relationship mapping with knowledge graph

- **Monitoring & Change Tracking** (Current Focus 🎯)

  - Real-time file tracking (in progress)
  - File versioning (in progress)
  - Notification system for changes (Completed ✅)

- **Expanded Format Support** (Planned)
  - Binary & specialized file support
  - Format conversion capabilities

### Phase 3: AI-Powered Enhancements (Planned)

- **AI-Powered Search & Recommendations**

  - ML-based search ranking
  - Context-aware search with NLP
  - Smart recommendations based on usage patterns

- **AI-Driven File Analysis**

  - Content classification with ML models
  - Pattern recognition for code and data
  - Anomaly detection for unusual file patterns

- **Distributed Processing & Scalability**
  - Microservices-based architecture
  - Load balancing for efficient task distribution
  - Sharding and replication for data consistency

### Phase 4: External Integrations & API (Planned)

- **API Development & External Integrations**

  - REST API with comprehensive endpoints
  - GraphQL support for flexible queries
  - Webhook-based triggers for automation

- **Plugin System & Extensibility**

  - Modular plugin architecture
  - Plugin isolation and security

- **Cloud & Deployment Enhancements**
  - Cloud storage support (S3, Google Cloud, Azure)
  - Cloud synchronization
  - Kubernetes deployment for auto-scaling

### Phase 5: Continuous Improvement (Planned)

- **Documentation & User Experience**

  - Technical documentation
  - Interactive tutorials

- **Testing & Quality Assurance**

  - Improve test coverage to >90%
  - Performance benchmarks with stress testing

- **Success Metrics**
  - Performance goals (search <100ms, processing >100MB/s)
  - Quality assurance (test coverage >90%, error rate <0.1%)

## Summary

The Aichemist Codex is a powerful tool for organizing, analyzing, and extracting
knowledge from your files. Its AI-powered features help you discover
relationships between files, automatically organize content, and efficiently
find information across your file collection. The system is designed to be both
powerful and flexible, with options to use it via command line or as a Python
library in your own applications. Currently in active development, the project
is focused on Phase 2 enhancements with real-time file tracking and versioning
as the current priorities.
