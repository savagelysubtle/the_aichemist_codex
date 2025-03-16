# PDF Metadata Extractor

## Overview

The PDF Metadata Extractor is a specialized component in The Aichemist Codex
metadata extraction framework that processes PDF documents and extracts
comprehensive information about their content, structure, and properties. This
extractor provides detailed insights into PDF files, enabling better document
organization, search, and analysis.

## Features

- **Document Properties**: Extracts standard PDF metadata fields like title,
  author, creation date, producer, etc.
- **Content Analysis**: Extracts and analyzes text content, including character
  count, word count, and line count.
- **Page Information**: Provides detailed information about page count,
  dimensions, and standard page sizes.
- **Font Detection**: Identifies and extracts information about fonts used in
  the document.
- **Image Analysis**: Detects embedded images and provides count estimates.
- **Security Analysis**: Determines if the document is encrypted and extracts
  permission information.
- **Scanned Document Detection**: Uses heuristics to identify if a PDF appears
  to be a scanned document.
- **Performance Optimization**: Implements sampling techniques for large
  documents to maintain efficiency.
- **Text Extraction**: Extracts readable text content with appropriate limits
  for large documents.
- **Caching Support**: Integrates with the caching system to improve performance
  for repeated extraction requests.

## Usage Examples

### Basic Usage

```python
from backend.src.metadata import PDFMetadataExtractor

# Create an instance of the extractor
pdf_extractor = PDFMetadataExtractor()

# Extract metadata from a PDF file
metadata = await pdf_extractor.extract("/path/to/document.pdf")

# Access specific metadata
title = metadata.get("document", {}).get("title", "Untitled")
page_count = metadata.get("structure", {}).get("page_count", 0)
word_count = metadata.get("content", {}).get("word_count", 0)

print(f"Document '{title}' has {page_count} pages and approximately {word_count} words.")
```

### Using With Cache Manager

```python
from backend.src.utils.cache_manager import CacheManager
from backend.src.metadata import PDFMetadataExtractor

# Create a cache manager
cache_manager = CacheManager()

# Initialize the extractor with caching support
pdf_extractor = PDFMetadataExtractor(cache_manager=cache_manager)

# Extract metadata (results will be cached)
metadata = await pdf_extractor.extract("/path/to/document.pdf")
```

### Handling Multiple PDF Files

```python
import asyncio
from pathlib import Path
from backend.src.metadata import PDFMetadataExtractor

async def process_pdf_directory(directory_path):
    pdf_extractor = PDFMetadataExtractor()
    results = {}

    # Process all PDF files in a directory
    for pdf_file in Path(directory_path).glob("*.pdf"):
        metadata = await pdf_extractor.extract(pdf_file)
        results[pdf_file.name] = metadata

    return results

# Process all PDFs in a directory
pdf_metadata = asyncio.run(process_pdf_directory("/path/to/pdf_documents/"))
```

## Extracted Metadata Structure

The extractor returns a dictionary with the following main sections:

### 1. `metadata_type`

Indicates the type of metadata ("pdf").

### 2. `document` Section

Contains document properties:

- `title`: Document title
- `author`: Document author
- `subject`: Document subject
- `keywords`: Document keywords
- `creator`: Application that created the document
- `producer`: Library/tool that produced the PDF
- `creation_date`: Date the document was created
- `modification_date`: Date the document was last modified
- `pdf_version`: PDF specification version
- `file_size`: Size of the PDF file in bytes

### 3. `structure` Section

Provides information about document structure:

- `page_count`: Total number of pages
- `pages`: Array of page information objects (dimensions, rotation, etc.)
- `uniform_page_size`: Boolean indicating if all pages have the same size
- `page_size`: Common page dimensions if uniform
- `standard_size`: Standard paper size (A4, Letter, etc.) if detected
- `fonts`: List of fonts used in the document
- `font_count`: Number of unique fonts
- `has_images`: Boolean indicating if images were detected
- `image_count_sampled`: Number of images found in sampled pages
- `image_count_estimated`: Estimated total image count (for large documents)

### 4. `content` Section

Contains content analysis:

- `character_count`: Total number of characters
- `word_count`: Approximate word count
- `line_count`: Approximate line count
- `average_word_length`: Average word length
- `full_text`: Complete extracted text (if not too large)
- `text_excerpt`: For large documents, contains beginning and ending excerpts
- `page_text`: Array of text excerpts from individual pages
- `appears_scanned`: Boolean indicating if the document appears to be scanned

### 5. `security` Section

Provides information about document security:

- `encrypted`: Boolean indicating if document is encrypted
- `encryption_method`: Encryption method if document is secured
- `permissions`: List of allowed operations
- `has_restrictions`: Boolean indicating if document has restrictions
- `owner_password_protected`: Boolean indicating if document requires owner
  password
- `user_password_protected`: Boolean indicating if document requires user
  password

## Supported Formats

The extractor supports the following MIME types:

- `application/pdf`
- `application/x-pdf`
- `application/acrobat`
- `application/vnd.pdf`

## Error Handling

The extractor includes comprehensive error handling for various scenarios:

- Non-existent files
- Corrupted PDF files
- Encryption/permission issues
- Memory limits for large documents

If the PDF cannot be processed, the result will include an `error` field with a
description of the issue.

## Performance Considerations

- For large PDFs (>10MB), the extractor limits text extraction to the first 50
  pages by default.
- Font and image analysis is sampled from a subset of pages to maintain
  performance.
- Text content is truncated for large documents, with only excerpts included in
  the metadata.
- The extractor uses caching to avoid repeated processing of the same unchanged
  file.

## Implementation Details

The extractor uses PyPDF2 for PDF parsing and extraction. If available, it also
uses pdf2image for additional functionality. The implementation handles various
PDF versions and structures, including:

- Different text encoding schemes in PDFs
- Various page layouts and structures
- Security and permission mechanisms
- Font embedding and subsetting
- Image formats within PDFs

## Integration with Other Components

The PDF Metadata Extractor integrates with the following system components:

- `CacheManager` for efficient caching
- `MimeTypeDetector` for file type identification
- `MetadataExtractorRegistry` for automatic registration

## Configuration

The extractor has several configurable parameters:

- `MAX_TEXT_EXTRACTION_SIZE`: Maximum file size for full text extraction
  (default: 10MB)
- `MAX_PAGES_FULL_EXTRACT`: Maximum pages to fully process in large documents
  (default: 50)

## Future Enhancements

Planned improvements include:

- OCR support for scanned documents
- Enhanced table detection and extraction
- Hyperlink and internal reference extraction
- Form field detection and analysis
- Signature validation and certificate extraction
- PDF/A compliance checking
- Improved image extraction and analysis

## Troubleshooting

Common issues and solutions:

- If text extraction yields unexpected results, the PDF might be scanned or have
  unusual encoding.
- For encrypted PDFs, only basic metadata can be extracted without the
  appropriate password.
- Memory issues with very large PDFs can be addressed by adjusting the
  MAX_TEXT_EXTRACTION_SIZE constant.
- If pdf2image functionality is unavailable, install the package with
  `pip install pdf2image`.
