# Enhanced Metadata Extraction

## Overview

The Enhanced Metadata Extraction feature adds powerful content analysis capabilities to The Aichemist Codex. It automatically extracts rich metadata from different file types using specialized extractors, enabling intelligent file categorization, tagging, and more advanced search capabilities.

## Key Components

### Core Framework

- **`BaseMetadataExtractor`**: Abstract base class defining the interface for all metadata extractors
- **`MetadataExtractorRegistry`**: Central registry for managing and selecting appropriate extractors for different file types
- **`MetadataManager`**: Coordinates metadata extraction across file types and manages batch processing

### Specialized Extractors

- **`TextMetadataExtractor`**: Analyzes plain text files to extract keywords, topics, entities, and more
- **`CodeMetadataExtractor`**: Processes source code files to detect language, imports, function/class definitions, and complexity metrics
- **`DocumentMetadataExtractor`**: Extracts metadata from document formats including authors, dates, versions, and document statistics

### Integration Points

- Enhanced `FileMetadata` class with additional metadata fields
- Integration with `FileReader.process_file()` for seamless metadata extraction during file processing
- Configuration settings in `settings.py` to control extraction behavior
- CLI commands for extracting and analyzing metadata

## Features

### Text Analysis

- **Language Detection**: Identifies the natural language of text content
- **Keyword Extraction**: Extracts important keywords and phrases using TF-IDF
- **Topic Modeling**: Discovers topics and themes in the content
- **Entity Extraction**: Identifies URLs, email addresses, dates, and phone numbers
- **Summary Generation**: Creates a brief summary of the content
- **Auto-tagging**: Generates tags based on the extracted information

### Code Analysis

- **Language Detection**: Identifies programming languages (25+ languages supported)
- **Import/Dependency Detection**: Extracts imported modules and packages
- **Function/Class Extraction**: Identifies function and class definitions
- **Complexity Metrics**: Calculates code complexity metrics (line count, comment percentage, cyclomatic complexity)
- **Framework Detection**: Recognizes common frameworks (Django, Flask, React, Angular, Vue)
- **Auto-tagging**: Generates tags based on language, complexity, and structure

### Document Analysis

- **Author Extraction**: Identifies document authors and contributors
- **Title/Subject Identification**: Extracts document titles and subjects
- **Date Extraction**: Detects creation and modification dates
- **Version Detection**: Identifies version information
- **Document Statistics**: Calculates word count, page count, paragraphs, and sections
- **Auto-tagging**: Generates tags based on document properties

## Usage

### Via CLI

```bash
# Extract metadata from a single file
python -m backend.cli metadata extract path/to/file.py

# Extract metadata from all files in a directory
python -m backend.cli metadata batch path/to/directory --recursive

# Extract metadata from specific file types
python -m backend.cli metadata batch path/to/directory --pattern "*.py"

# Analyze files and group by metadata properties
python -m backend.cli metadata analyze path/to/directory --group-by language
```

### Via API

```python
from backend.file_reader.file_reader import FileReader
from backend.utils.cache_manager import CacheManager

# Initialize the file reader with caching
cache_manager = CacheManager()
file_reader = FileReader(cache_manager=cache_manager)

# Process a file to extract metadata
metadata = await file_reader.process_file("path/to/file.py")

# Access extracted metadata
print(f"Language: {metadata.code_language}")
print(f"Functions: {metadata.functions}")
print(f"Tags: {metadata.tags}")
```

## Performance Considerations

- **Caching**: Results are cached to avoid repeated extraction for the same file
- **Async Processing**: All extraction operations are asynchronous for better performance
- **Concurrency Control**: Batch extraction limits concurrency to prevent system overload
- **Configurable Settings**: Extraction behavior can be configured through settings

## Extension Points

The metadata extraction system is designed to be extensible:

1. Create a new extractor class that inherits from `BaseMetadataExtractor`
2. Implement the required methods and register it with the `MetadataExtractorRegistry`
3. The system will automatically use your extractor for the MIME types it supports