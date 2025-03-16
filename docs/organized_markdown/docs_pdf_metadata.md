# PDF Metadata Extractor

## Overview

The PDF Metadata Extractor is a specialized component of The Aichemist Codex
that extracts rich metadata from PDF documents. It provides comprehensive
information about PDF files, including document properties, structure, content
characteristics, security settings, and embedded resources. This capability
enables intelligent analysis, search, and organization of PDF documents within
knowledge management systems.

## Features

- **Document Properties Extraction**: Extracts standard PDF document properties
  like title, author, creation date, producer, and keywords
- **Page Structure Analysis**: Provides detailed information about page count,
  dimensions, and rotation angles
- **Text Content Analysis**: Analyzes text content presence and density across
  the document
- **Font Detection**: Identifies embedded fonts used in the document
- **Embedded Resource Detection**: Detects the presence of images, forms, and
  other embedded resources
- **Security Analysis**: Extracts information about encryption status and
  password protection
- **PDF Version Detection**: Identifies the PDF specification version
- **Format Auto-detection**: Automatically validates PDF files based on MIME
  type or file extension
- **Caching Support**: Integrates with the cache management system for improved
  performance
- **Error Handling**: Provides robust error handling for corrupted or invalid
  PDF files

## Usage Examples

### Basic Usage

```python
from backend.src.metadata import PDFMetadataExtractor

# Create an instance of the extractor
pdf_extractor = PDFMetadataExtractor()

# Extract metadata from a PDF file
metadata = await pdf_extractor.extract("path/to/document.pdf")

# Access extracted information
title = metadata["document_info"].get("Title")
page_count = metadata["structure"]["page_count"]
is_encrypted = metadata["security"]["encrypted"]
has_images = metadata["embedded_resources"]["has_images"]
```

### Using with Cache Manager

```python
from backend.src.metadata import PDFMetadataExtractor
from backend.src.utils.cache_manager import CacheManager

# Create a cache manager
cache_manager = CacheManager()

# Create an extractor with caching
pdf_extractor = PDFMetadataExtractor(cache_manager=cache_manager)

# Extract metadata (will be cached)
metadata = await pdf_extractor.extract("path/to/document.pdf")

# Subsequent extractions of the same file will use cached data
metadata_again = await pdf_extractor.extract("path/to/document.pdf")
```

### Processing Multiple PDF Files

```python
import os
from backend.src.metadata import PDFMetadataExtractor

pdf_extractor = PDFMetadataExtractor()
results = []

# Process all PDF files in a directory
for filename in os.listdir("documents/"):
    if filename.lower().endswith(".pdf"):
        file_path = os.path.join("documents/", filename)
        try:
            metadata = await pdf_extractor.extract(file_path)
            results.append(metadata)
        except Exception as e:
            print(f"Error processing {filename}: {e}")
```

## Extracted Metadata Structure

The PDF metadata extractor returns a dictionary with the following structure:

```
{
    "metadata_type": "pdf",
    "filename": "document.pdf",
    "file_size": 123456,
    "document_info": {
        "Title": "Sample Document",
        "Author": "John Doe",
        "CreationDate": "2023-01-01T12:00:00",
        "Producer": "PDF Producer",
        "Keywords": "sample, document, pdf"
    },
    "structure": {
        "page_count": 10,
        "pages": [
            {
                "page_number": 1,
                "width": 612.0,
                "height": 792.0,
                "rotation": 0,
                "text_length": 2500,
                "has_text": true
            },
            // Additional pages...
        ]
    },
    "security": {
        "encrypted": false,
        "has_user_password": false,
        "permissions": null
    },
    "embedded_resources": {
        "has_images": true,
        "has_fonts": true,
        "has_forms": false
    },
    "pdf_version": "PDF-1.7",
    "extraction_method": "pypdf"
}
```

## Supported Formats

The PDF Metadata Extractor supports PDF files with the following MIME types:

- `application/pdf`

It can handle various PDF specification versions, including PDF 1.0 through PDF
2.0.

## Extraction Methods

The extractor primarily uses PyPDF2 for metadata extraction. This library
provides comprehensive access to PDF document structure and metadata.

## Error Handling

The extractor provides robust error handling for various scenarios:

- **Non-existent Files**: Raises `FileNotFoundError` when the specified file
  doesn't exist
- **Unsupported Formats**: Raises `ValueError` when attempting to extract
  metadata from non-PDF files
- **Corrupted PDFs**: Handles corrupted PDF files gracefully, returning an error
  message without crashing
- **Missing Dependencies**: Checks for required dependencies and provides clear
  error messages if they're missing

## Performance Considerations

- **Caching**: The extractor supports caching extracted metadata to avoid
  redundant processing of the same file
- **Large Files**: For large PDF files, the extractor applies heuristics to
  limit text extraction to prevent excessive memory usage
- **Password-Protected Files**: Limited metadata can be extracted from encrypted
  files even without the password

## Dependencies

- **PyPDF2**: Primary library for PDF parsing and metadata extraction (required)
- **pdf2image** (optional): For enhanced image extraction capabilities when
  available

## Integration with Other Components

The PDF Metadata Extractor integrates with several other components in The
Aichemist Codex:

- **Cache Manager**: For caching extraction results
- **MIME Type Detector**: For automatic file format validation
- **Metadata Extractor Registry**: For automatic registration and discovery

## Troubleshooting

### Common Issues

- **Extraction Fails with "PyPDF2 is required" Error**: Ensure PyPDF2 is
  installed with `pip install PyPDF2`
- **Corrupted PDF Files**: If extraction fails with PDF structure errors, the
  file may be corrupted
- **Memory Errors with Large Files**: For very large PDF files, consider
  increasing available memory or processing the file in segments

## Future Enhancements

- Add support for extracting embedded images from PDF files
- Implement OCR capabilities for scanned PDF documents
- Enhance text analysis with natural language processing
- Add ability to extract structured data from PDF forms
- Improve handling of PDF/A and other specialized PDF formats
