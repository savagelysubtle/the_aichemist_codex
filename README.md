# The Aichemist Codex

A modular file and project management system designed for developers, researchers, and data analysts.

## Features

- Comprehensive file tree generation with detailed statistics
- Code summarization for Python projects
- Advanced regex-based search across multiple files
- Semantic search using vector embeddings
- Similarity search for finding related files
- **Enhanced metadata extraction for files**:
  - Text analysis (keywords, topics, entities)
  - Code analysis (language, imports, functions, classes, complexity)
  - Document analysis (authors, dates, version, statistics)
- Metadata-based filtering
- Rule-based file sorting and organization
- Duplicate file detection
- File change monitoring
- Jupyter notebook conversion
- Token counting for AI model inputs
- Project digests for quick overviews

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

### Command-line Interface

The Aichemist Codex provides a comprehensive CLI for all its functionality:

```bash
# Generate a file tree
python -m backend.cli tree /path/to/directory --output tree.json

# Summarize Python code
python -m backend.cli summarize /path/to/directory --output-format md

# Search files
python -m backend.cli search /path/to/directory "search pattern"

# Extract metadata from a file
python -m backend.cli metadata extract /path/to/file.py

# Extract metadata from all files in a directory
python -m backend.cli metadata batch /path/to/directory --recursive

# Analyze files and group by metadata properties
python -m backend.cli metadata analyze /path/to/directory --group-by tags

# Sort files according to rules
python -m backend.cli sort /path/to/directory --config sort_rules.json

# Find duplicate files
python -m backend.cli duplicates /path/to/directory

# Find similar files
python -m backend.cli similarity find /path/to/file.py /path/to/directory

# Monitor file changes
python -m backend.cli watch /path/to/directory

# Convert Jupyter notebooks to Python
python -m backend.cli notebooks convert /path/to/notebook.ipynb

# Count tokens for AI models
python -m backend.cli tokens /path/to/directory

# Generate project digest
python -m backend.cli ingest /path/to/directory
```

## Enhanced Metadata Extraction

The Aichemist Codex includes a powerful metadata extraction system that provides rich information about your files. The system automatically selects the appropriate extractor based on file type:

### Text Files

For text files, the system extracts:
- Language detection
- Keywords and key phrases
- Topic modeling
- Entity extraction (URLs, emails, dates, etc.)
- Automatic tagging

### Code Files

For code files, the system extracts:
- Programming language detection
- Imports and dependencies
- Function and class definitions
- Complexity metrics (line count, cyclomatic complexity, comment ratio)
- Framework detection (e.g., Django, Flask, React)
- Automatic tagging based on code properties

### Documents

For document files, the system extracts:
- Authors and contributors
- Creation and modification dates
- Version information
- Document statistics (word count, page count, section count)
- Automatic tagging based on document properties

### Usage Examples

```bash
# Extract metadata from a Python file
python -m backend.cli metadata extract /path/to/file.py

# Extract metadata from all Python files in a directory
python -m backend.cli metadata batch /path/to/directory --pattern "*.py"

# Group files by programming language
python -m backend.cli metadata analyze /path/to/directory --group-by language

# Group files by author
python -m backend.cli metadata analyze /path/to/directory --group-by authors
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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

```

