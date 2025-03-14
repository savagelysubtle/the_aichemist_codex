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
- Example usage:
  ```python
  reader = FileReader(max_workers=2, preview_length=100)
  metadata = await reader.process_file(file_path)
  mime_type = reader.get_mime_type(file_path)
  ```

### 2. File Metadata (file_metadata.py)

- Data structure for file information
- Attributes:
  - path: File location
  - mime_type: Detected MIME type
  - size: File size in bytes
  - extension: File extension
  - preview: Content preview
  - error: Error information
  - parsed_data: Structured content

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

### Parsing Features

- MIME type detection
- Content preview generation
- Metadata extraction
- Error handling
- Asynchronous operations
- Binary file support

### File Type Support

- Text-based formats
- Binary formats
- Archive formats
- Image formats
- Document formats
- Code formats

## Integration Points

### Internal Dependencies

- Utils package for async I/O
- Config package for settings
- Safety checks and validation

### External Dependencies

- python-magic for MIME detection
- pandas for spreadsheet parsing
- PyPDF2 for PDF processing
- python-docx for Word documents
- PyYAML for YAML parsing
- kreuzberg for OCR processing

## Best Practices

### File Reading

```python
# Process single file
metadata = await reader.process_file(file_path)

# Process multiple files
results = await reader.read_files([file_path1, file_path2])

# Get MIME types
mime_types = reader.get_mime_types([file_path1, file_path2])
```

### Error Handling

```python
try:
    metadata = await reader.process_file(file_path)
    if metadata.error:
        logger.error(f"Error processing {file_path}: {metadata.error}")
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
