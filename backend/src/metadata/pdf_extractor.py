"""
Module for extracting metadata from PDF files.

This module provides functionality for extracting metadata from PDF files,
including basic document properties, content structure, and embedded resources.
"""

import logging
import os
import typing as t
from datetime import datetime
from pathlib import Path

# Third-party imports - PyPDF2
try:
    from PyPDF2 import PdfReader
    from PyPDF2.errors import PdfReadError

    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    PdfReader = None
    PdfReadError = Exception  # Fallback type

# Local application imports
from backend.src.file_reader.file_metadata import FileMetadata
from backend.src.metadata.extractor import (
    BaseMetadataExtractor,
    MetadataExtractorRegistry,
)
from backend.src.utils.cache_manager import CacheManager
from backend.src.utils.mime_type_detector import MimeTypeDetector

logger = logging.getLogger(__name__)


@MetadataExtractorRegistry.register
class PDFMetadataExtractor(BaseMetadataExtractor):
    """
    Extractor for PDF file metadata.

    This class handles the extraction of metadata from PDF files, including:
    - Document properties (title, author, creation date)
    - Page count and dimensions
    - Text content analysis
    - Embedded resources (images, fonts)
    - Security settings
    - PDF version information
    """

    # Supported MIME types
    SUPPORTED_MIME_TYPES = ["application/pdf"]

    # File extensions to MIME types mapping
    FILE_EXTENSIONS = {".pdf": "application/pdf"}

    def __init__(self, cache_manager: CacheManager | None = None) -> None:
        """
        Initialize the PDF metadata extractor.

        Args:
            cache_manager: Optional cache manager for caching extracted metadata.
        """
        super().__init__(cache_manager)
        self.mime_detector = MimeTypeDetector()

    @property
    def supported_mime_types(self) -> list[str]:
        """Get the list of MIME types this extractor supports.

        Returns:
            List of supported MIME types
        """
        return self.SUPPORTED_MIME_TYPES

    def _extract_pdf_with_pypdf(self, file_path: str) -> dict[str, t.Any]:
        """
        Extract metadata from PDF files using PyPDF2.

        Args:
            file_path: Path to the PDF file.

        Returns:
            Dictionary containing extracted metadata.

        Raises:
            PdfReadError: If the PDF file cannot be read or is corrupted.
        """
        # Check that PdfReader is available before using it
        if not PYPDF2_AVAILABLE or PdfReader is None:
            raise ImportError("PyPDF2 is required for PDF metadata extraction")

        try:
            pdf = PdfReader(file_path)

            # Extract document information
            metadata = {}
            if pdf.metadata:
                for key, value in pdf.metadata.items():
                    # Clean up the key (remove leading '/')
                    clean_key = key.strip("/") if isinstance(key, str) else key
                    metadata[clean_key] = value

            # Format dates if available
            for date_field in ["CreationDate", "ModDate"]:
                if date_field in metadata:
                    try:
                        # PDF dates are typically in format: D:YYYYMMDDHHmmSS
                        date_str = metadata[date_field]
                        if isinstance(date_str, str) and date_str.startswith("D:"):
                            date_str = date_str[2:]  # Remove 'D:' prefix
                            if len(date_str) >= 14:
                                year = int(date_str[0:4])
                                month = int(date_str[4:6])
                                day = int(date_str[6:8])
                                hour = int(date_str[8:10])
                                minute = int(date_str[10:12])
                                second = int(date_str[12:14])

                                formatted_date = datetime(
                                    year, month, day, hour, minute, second
                                ).isoformat()
                                metadata[date_field] = formatted_date
                    except (ValueError, TypeError):
                        # Keep original value if parsing fails
                        pass

            # Extract document structure information
            structure_info = {"page_count": len(pdf.pages), "pages": []}

            # Extract information for each page
            for i, page in enumerate(pdf.pages):
                page_info = {
                    "page_number": i + 1,
                }

                # Get rotation if available
                try:
                    if hasattr(page, "get"):
                        page_info["rotation"] = page.get("/Rotate", 0)
                    else:
                        # Fallback for different PyPDF2 versions
                        page_info["rotation"] = 0
                except Exception:
                    page_info["rotation"] = 0

                # Get page dimensions if available
                try:
                    if hasattr(page, "mediabox"):
                        # Newer PyPDF2 versions
                        page_info["width"] = int(page.mediabox.width)
                        page_info["height"] = int(page.mediabox.height)
                    elif hasattr(page, "/MediaBox"):
                        # Older PyPDF2 versions or different access pattern
                        media_box = page["/MediaBox"]
                        if (
                            hasattr(media_box, "__len__")
                            and len(t.cast(t.Sequence[float], media_box)) == 4
                        ):
                            media_box_seq = t.cast(t.Sequence[float], media_box)
                            width = float(media_box_seq[2]) - float(media_box_seq[0])
                            height = float(media_box_seq[3]) - float(media_box_seq[1])
                            page_info["width"] = int(width)
                            page_info["height"] = int(height)
                except (AttributeError, KeyError, TypeError) as e:
                    logger.warning(f"Failed to extract page dimensions: {e}")

                # Extract text length as a content indicator
                try:
                    text = page.extract_text()
                    page_info["text_length"] = len(text)
                    page_info["has_text"] = len(text.strip()) > 0
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {i + 1}: {e}")
                    page_info["text_length"] = 0
                    page_info["has_text"] = False

                structure_info["pages"].append(page_info)

            # Analyze security features
            security_info = {
                "encrypted": pdf.is_encrypted,
                "has_user_password": False,
                "permissions": None,
            }

            if pdf.is_encrypted:
                # Check if there's a user password
                security_info["has_user_password"] = True
                # Note: Permissions extraction is PyPDF2 version dependent
                # We'll try our best but may not work across all versions

            # Analyze file for embedded objects
            embedded_resources = {
                "has_images": False,
                "has_fonts": False,
                "has_forms": False,
            }

            try:
                # Sample a few pages to check for resources
                sample_pages = min(5, len(pdf.pages))
                for i in range(sample_pages):
                    page = pdf.pages[i]

                    # Check for resources - PyPDF2 version-independent approach
                    if hasattr(page, "get") and page.get("/Resources"):
                        resources = page["/Resources"]

                        # Check for fonts
                        if t.cast(dict, resources).get("/Font"):
                            embedded_resources["has_fonts"] = True

                        # Check for images
                        if t.cast(dict, resources).get("/XObject"):
                            xobjects = t.cast(dict, resources)["/XObject"]
                            for _, xobject in t.cast(dict, xobjects).items():
                                if (
                                    hasattr(xobject, "get")
                                    and xobject.get("/Subtype") == "/Image"
                                ):
                                    embedded_resources["has_images"] = True
                                    break
            except Exception as e:
                logger.warning(f"Failed to analyze embedded resources: {e}")

            # Compile the final metadata structure
            result = {
                "metadata_type": "pdf",
                "filename": os.path.basename(file_path),
                "file_size": os.path.getsize(file_path),
                "document_info": metadata,
                "structure": structure_info,
                "security": security_info,
                "embedded_resources": embedded_resources,
                "pdf_version": pdf.pdf_header if hasattr(pdf, "pdf_header") else None,
                "extraction_method": "pypdf",
            }

            return result

        except PdfReadError as e:
            logger.error(f"Error reading PDF file {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing PDF file {file_path}: {e}")
            raise

    async def extract(
        self,
        file_path: str | Path,
        content: str | None = None,
        mime_type: str | None = None,
        metadata: FileMetadata | None = None,
    ) -> dict[str, t.Any]:
        """
        Extract metadata from a PDF file.

        Args:
            file_path: Path to the PDF file
            content: Not used for PDF files
            mime_type: Optional MIME type of the file
            metadata: Optional existing metadata to enhance

        Returns:
            Dictionary containing extracted PDF metadata

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is not a supported PDF format.
        """
        # Convert to Path for consistent handling
        path = Path(file_path)
        if not path.exists():
            error_message = f"File does not exist: {path}"
            logger.error(error_message)
            raise FileNotFoundError(error_message)

        # Determine MIME type if not provided
        if mime_type is None:
            mime_type, _ = self.mime_detector.get_mime_type(path)

        # Verify that this is a PDF file
        if mime_type not in self.supported_mime_types:
            # Fallback to extension-based detection if MIME type detection fails
            extension = path.suffix.lower()
            if extension in self.FILE_EXTENSIONS:
                logger.debug(
                    f"MIME type detection failed, using extension {extension} "
                    f"for {path}"
                )
            else:
                error_message = (
                    f"Unsupported file format: {mime_type} for {path}. "
                    f"PDFMetadataExtractor supports: "
                    f"{', '.join(self.supported_mime_types)}"
                )
                logger.error(error_message)
                raise ValueError(error_message)

        # Try to use cache if available
        if self.cache_manager:
            cache_key = f"pdf_metadata:{path}:{path.stat().st_mtime}"
            cached_data = await self.cache_manager.get(cache_key)
            if cached_data:
                logger.debug(f"Using cached PDF metadata for {path}")
                return cached_data

        try:
            # Extract metadata using PyPDF2
            result = self._extract_pdf_with_pypdf(str(path))

            # Cache the result if cache manager is available
            if self.cache_manager:
                await self.cache_manager.put(cache_key, result)

            return result
        except Exception as e:
            error_message = f"Failed to extract metadata from {path}: {e}"
            logger.error(error_message)
            # Return basic error information instead of raising
            return {
                "metadata_type": "pdf",
                "error": f"Error extracting PDF metadata: {str(e)}",
            }
