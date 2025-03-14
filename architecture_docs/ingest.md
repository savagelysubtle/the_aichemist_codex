Here's the updated content for modules/ingest.md:

```markdown
# Ingest Package Documentation

## Overview
The Ingest package provides comprehensive file ingestion capabilities, handling directory scanning, file content extraction, and content aggregation. It supports multiple file formats with special handling for Jupyter notebooks and implements efficient token counting and size formatting.

## Components

### 1. Reader (reader.py)
- Core functionality for file content extraction
- Features:
  - Full file content reading
  - Multiple encoding support
  - Jupyter notebook conversion
  - Configurable options handling
- Key functions:
  ```python
  def read_full_file(file_path: Path) -> str:
      """Reads entire file content with encoding handling"""

  def convert_notebook(notebook_path: Path, include_output: bool = True) -> str:
      """Converts Jupyter notebooks to text format"""

  def generate_digest(source_dir: Path, options: Optional[Dict[str, Any]] = None) -> str:
      """Generates complete project digest"""
  ```

### 2. Scanner (scanner.py)

- Directory traversal and file filtering
- Features:
  - Recursive directory scanning
  - Pattern-based inclusion/exclusion
  - Safe file handling integration
  - Directory traversal safety
- Example usage:

  ```python
  files = scan_directory(
      directory=Path("project_dir"),
      include_patterns={"*.py", "*.md"},
      ignore_patterns={"*.pyc", "__pycache__"}
  )
  ```

### 3. Aggregator (aggregator.py)

- Content combination and formatting
- Features:
  - Token counting using tiktoken
  - Human-readable size formatting
  - Content aggregation
  - Summary statistics
- Key functions:

  ```python
  def count_tokens(context_string: str) -> int:
      """Counts tokens using cl100k_base encoding"""

  def human_readable_size(size: int) -> str:
      """Converts bytes to human-readable format"""

  def aggregate_digest(file_paths: List[Path], content_map: Dict[Path, str]) -> str:
      """Creates comprehensive content digest"""
  ```

## Implementation Details

### File Reading Process

1. Directory Scanning
   - Pattern-based file filtering
   - Safe traversal with depth limits
   - Ignore pattern application

2. Content Extraction
   - UTF-8 encoding (primary)
   - Latin-1 fallback encoding
   - Special handling for notebooks
   - Error handling and logging

3. Content Aggregation
   - Token counting
   - Size calculation
   - Content formatting
   - Summary generation

### Jupyter Notebook Handling

- Cell type recognition
- Code cell processing
- Markdown cell handling
- Optional output inclusion
- Format preservation

### Safety Features

- Safe file handling
- Pattern validation
- Size limits
- Encoding fallbacks
- Error recovery

## Integration Points

### Internal Dependencies

- Utils package for safety checks
- File Reader for content extraction
- Config for settings

### External Dependencies

- tiktoken for token counting
- pathlib for path handling
- typing for type hints

## Best Practices

### Directory Scanning

```python
# Basic scanning
files = scan_directory(source_dir)

# With patterns
files = scan_directory(
    source_dir,
    include_patterns={"*.py", "*.md"},
    ignore_patterns={"test_*", "*.pyc"}
)
```

### Content Generation

```python
# Generate project digest
digest = generate_digest(
    source_dir,
    options={
        "include_patterns": {"*"},
        "ignore_patterns": set(),
        "include_notebook_output": True
    }
)
```

### Error Handling

```python
try:
    content = read_full_file(file_path)
except UnicodeDecodeError:
    # Fallback to alternative encoding
    content = read_full_file_with_encoding(file_path, "latin-1")
```

## Future Improvements

### Short-term

1. Enhanced encoding detection
2. Additional file format support
3. Improved notebook handling
4. Better error recovery
5. Extended pattern matching

### Long-term

1. Streaming content processing
2. Parallel file processing
3. Content caching system
4. Advanced token analysis
5. Format conversion capabilities

```

This documentation accurately reflects the current implementation while providing clear examples and usage patterns. It covers all major components and their interactions, making it easier for developers to understand and use the ingestion system effectively.
