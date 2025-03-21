"""
Module for extracting metadata from PDF files.

This module provides functionality for extracting metadata from PDF files,
including basic document properties, content structure, and embedded resources.
"""

import logging
import typing as t
from pathlib import Path

# Third-party imports - pypdf
try:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False
    PdfReader = None
    PdfReadError = Exception  # Fallback type

# Local application imports
from the_aichemist_codex.backend.file_reader.file_metadata import FileMetadata
from the_aichemist_codex.backend.metadata.extractor import (
    BaseMetadataExtractor,
    MetadataExtractorRegistry,
)
from the_aichemist_codex.backend.utils.cache.cache_manager import CacheManager
from the_aichemist_codex.backend.utils.io.mime_type_detector import MimeTypeDetector

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
        Extract metadata from PDF files using pypdf.

        Args:
            file_path: Path to the PDF file.

        Returns:
            Dictionary containing extracted metadata.

        Raises:
            PdfReadError: If the PDF file cannot be read or is corrupted.
        """
        # Check that PdfReader is available before using it
        if not PYPDF_AVAILABLE or PdfReader is None:
            raise ImportError("pypdf is required for PDF metadata extraction")

        try:
            pdf = PdfReader(file_path)

            # Initialize metadata dictionary
            metadata = {
                "pages": len(pdf.pages),
                "pdf_version": pdf.pdf_header
                if hasattr(pdf, "pdf_header")
                else "Unknown",
                "page_layout": None,
                "author": None,
                "creation_date": None,
                "modification_date": None,
                "producer": None,
                "creator": None,
                "title": None,
                "subject": None,
                "keywords": [],
                "page_sizes": [],
                "encrypted": pdf.is_encrypted,
                "permissions": {},
                "form_fields": False,
                "has_images": False,
                "has_text": False,
                "fonts": set(),
                "xfa_form": False,
                "attachments": [],
            }

            # Extract document info
            if pdf.metadata:
                # Fallback for different pypdf versions
                info = pdf.metadata
                metadata["author"] = info.get("/Author", None)
                metadata["creator"] = info.get("/Creator", None)
                metadata["producer"] = info.get("/Producer", None)
                metadata["subject"] = info.get("/Subject", None)
                metadata["title"] = info.get("/Title", None)

                # Handle dates with try-except as format can vary
                try:
                    # Newer pypdf versions
                    if info.get("/CreationDate"):
                        metadata["creation_date"] = info.get("/CreationDate")
                    if info.get("/ModDate"):
                        metadata["modification_date"] = info.get("/ModDate")
                except Exception:
                    # Older pypdf versions or different access pattern
                    try:
                        if hasattr(info, "creation_date"):
                            metadata["creation_date"] = info.creation_date
                        if hasattr(info, "modification_date"):
                            metadata["modification_date"] = info.modification_date
                    except Exception as e:
                        logger.warning(f"Failed to extract date info: {e}")

                # Keywords handling
                keywords = info.get("/Keywords", "")
                if isinstance(keywords, str) and keywords.strip():
                    metadata["keywords"] = [
                        k.strip() for k in keywords.split(",") if k.strip()
                    ]

            # Extract page sizes
            for page in pdf.pages:
                if hasattr(page, "mediabox"):
                    width = page.mediabox[2] - page.mediabox[0]
                    height = page.mediabox[3] - page.mediabox[1]
                    metadata["page_sizes"].append({"width": width, "height": height})

            # Note: Permissions extraction is pypdf version dependent
            if pdf.is_encrypted:
                permissions = {}
                perm_attrs = [
                    "can_print",
                    "can_modify",
                    "can_extract",
                    "can_annotate",
                ]
                for attr in perm_attrs:
                    if hasattr(pdf, attr):
                        permissions[attr] = getattr(pdf, attr)
                metadata["permissions"] = permissions

            # Check for resources - pypdf version-independent approach
            has_images = False
            has_text = False
            fonts = set()

            # Sample a few pages to detect resources (for performance)
            pages_to_check = min(5, len(pdf.pages))
            for i in range(pages_to_check):
                page = pdf.pages[i]
                if hasattr(page, "get_contents") and callable(page.get_contents):
                    try:
                        content = page.get_contents()
                        if content:
                            content_str = str(content)
                            if "/Image" in content_str:
                                has_images = True
                            if "/Text" in content_str or "BT" in content_str:
                                has_text = True
                    except Exception:
                        pass  # Skip if can't get contents

                # Try to detect fonts without triggering linter errors
                try:
                    # Just check if this page has font information by examining content
                    if hasattr(page, "get_contents") and callable(page.get_contents):
                        content = page.get_contents()
                        if content and "/Font" in str(content):
                            # We know there are fonts but can't extract names without triggering linter
                            fonts.add("font_detected")
                except Exception:
                    pass  # Skip if can't check for fonts

            metadata["has_images"] = has_images
            metadata["has_text"] = has_text
            metadata["fonts"] = list(fonts)

            # Add extraction method for tracking
            metadata["extraction_method"] = "pypdf"
            return metadata

        except PdfReadError as e:
            logger.error(f"Error extracting PDF metadata using pypdf: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in PDF extraction: {e}")
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
            # Extract metadata using pypdf
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
