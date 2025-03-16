Here's the updated content for modules/file_reader.md:

```markdown
# File Reader Package Documentation

## Overview
The File Reader package provides comprehensive file reading and parsing capabilities with support for multiple file formats. It implements MIME type detection, asynchronous I/O operations, and specialized parsers for various file types including documents, spreadsheets, code files, and images with OCR support.

## Components

### 1. File Reader (file_reader.py)
- Core class for file reading and MIME type detection
- Features:
  - Asynchronous file operations
  - MIME type detection using python-magic
  - Preview generation
  - Error handling and logging
  - Concurrent processing support
  - Caching support
- Example usage:
  ```python
  # Initialize with optional cache manager
  reader = FileReader(max_workers=2, preview_length=100, cache_manager=cache_instance)

  # Process a single file
  metadata = await reader.process_file(file_path)

  # Get MIME type
  mime_type = reader.get_mime_type(file_path)

  # Process multiple files
  results = await reader.read_files([file_path1, file_path2])
  ```

### 2. File Metadata (file_metadata.py)

- Rich data structure for file information
- Core Attributes:
  - path: File location
  - mime_type: Detected MIME type
  - size: File size in bytes
  - extension: File extension
  - preview: Content preview
  - error: Error information
  - parsed_data: Structured content
- Content-based Attributes:
  - tags: Automatic content tags
  - keywords: Extracted keywords
  - topics: Topic distribution with scores
  - entities: Named entities by category
  - language: Detected language
  - content_type: Type of content
  - category: Content category
  - summary: Auto-generated summary
- Code File Attributes:
  - programming_language: Detected language
  - imports: Extracted import statements
  - functions: Function definitions
  - classes: Class definitions
  - complexity_score: Code complexity rating
- Document Attributes:
  - title: Document title
  - author: Document author
  - creation_date: Creation timestamp
  - modified_date: Last modification date
- Extraction Metadata:
  - extraction_complete: Process completion flag
  - extraction_confidence: Confidence score
  - extraction_time: Processing duration

### 3. Parsers (parsers.py)

Comprehensive parsing system with specialized parsers for different file types:

#### Text Files

- Plain text (TXT)
- Markdown (MD)
- CSV files
- XML documents
- YAML files
- JSON data

#### Documents

- PDF files
- Microsoft Word (DOCX)
- OpenDocument Text
- EPUB documents

#### Spreadsheets

- CSV files
- Excel (XLSX)
- OpenDocument Spreadsheets (ODS)

#### Code Files

- Python source code
- JavaScript files
- Configuration files (JSON, YAML, TOML)
- XML documents

#### Vector/CAD Files

- DWG files
- DXF files
- SVG graphics

#### Archives

- ZIP files
- TAR archives
- RAR archives
- 7Z archives
- Gzip and Bzip2 files

### 4. OCR Parser (ocr_parser.py)

- Image text extraction capabilities
- Features:
  - Asynchronous OCR processing
  - Text content extraction
  - Preview generation
  - Error handling
- Uses kreuzberg library for OCR

## Implementation Details

### File Reader Implementation

```python
class FileReader:
    def __init__(
        self,
        max_workers: int = 2,
        preview_length: int = 100,
        cache_manager: CacheManager | None = None,
    ):
        """Initialize FileReader with optional caching."""

    def get_mime_type(self, file_path: str | Path) -> str:
        """Detect MIME type with fallback mechanisms."""

    async def read_files(self, file_paths: list[Path]) -> list[FileMetadata]:
        """Process multiple files concurrently."""

    async def process_file(self, file_path: Path) -> FileMetadata:
        """Extract metadata, preview, and content from a file."""
```

### FileMetadata Structure

```python
@dataclass
class FileMetadata:
    # Core attributes
    path: Path
    mime_type: str
    size: int
    extension: str
    preview: str
    error: str | None = None
    parsed_data: Any | None = None

    # Content-based metadata fields
    tags: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    topics: list[dict[str, float]] = field(default_factory=list)
    entities: dict[str, list[str]] = field(default_factory=dict)
    language: str | None = None
    content_type: str | None = None
    category: str | None = None
    summary: str | None = None

    # For code files
    programming_language: str | None = None
    imports: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    complexity_score: float | None = None

    # For document files
    title: str | None = None
    author: str | None = None
    creation_date: str | None = None
    modified_date: str | None = None

    # Extraction metadata
    extraction_complete: bool = False
    extraction_confidence: float = 0.0
    extraction_time: float = 0.0
```

### Parser Base Class

```python
class BaseParser(ABC):
    @abstractmethod
    async def parse(self, file_path: Path) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_preview(self, parsed_data: Dict[str, Any], max_length: int = 1000) -> str:
        pass
```

## Integration Points

### Internal Dependencies

- Utils package for async I/O and caching
- Config package for settings
- Metadata manager for persistent storage
- Safety checks and validation

### External Dependencies

- python-magic for MIME detection
- pandas for spreadsheet parsing
- PyPDF2 for PDF processing
- python-docx for Word documents
- PyYAML for YAML parsing
- kreuzberg for OCR processing

## Best Practices

### Efficient File Processing

```python
# Process files with caching
cache_manager = CacheManager()
reader = FileReader(cache_manager=cache_manager)

# Process single file with cached results
metadata = await reader.process_file(file_path)

# Process multiple files concurrently
results = await reader.read_files([file_path1, file_path2])
```

### Error Handling

```python
try:
    metadata = await reader.process_file(file_path)
    if metadata.error:
        logger.error(f"Error processing {file_path}: {metadata.error}")
    else:
        # Check extraction completion and confidence
        if not metadata.extraction_complete or metadata.extraction_confidence < 0.7:
            logger.warning(f"Low confidence extraction for {file_path}")
except Exception as e:
    logger.error(f"Failed to process file: {e}")
```

## Future Improvements

### Short-term

1. Enhanced OCR capabilities
2. Additional file format support
3. Improved preview generation
4. Better error recovery
5. Extended metadata extraction

### Long-term

1. Machine learning-based content analysis
2. Advanced text extraction
3. Format conversion capabilities
4. Streaming file processing
5. Cloud storage integration

```

This documentation accurately reflects the current implementation while providing clear examples and usage patterns. It covers all major components and their interactions, making it easier for developers to understand and use the file reading system effectively.
