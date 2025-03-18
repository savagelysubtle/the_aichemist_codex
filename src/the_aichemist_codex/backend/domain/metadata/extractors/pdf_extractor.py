import logging
import os
from typing import Any

from ....core.exceptions import ExtractorError
from ..extractor import Extractor

logger = logging.getLogger(__name__)


class PDFExtractor(Extractor):
    """Extractor for PDF files."""

    def __init__(self):
        super().__init__()
        self._supported_extensions = {".pdf"}
        self._supported_mime_types = {"application/pdf"}

        # Check if required libraries are available
        self._has_pypdf = self._check_pypdf()
        if not self._has_pypdf:
            logger.warning("pypdf library not found. PDF extraction will be limited.")

    def _check_pypdf(self) -> bool:
        """Check if pypdf library is available.

        Returns:
            True if the library is available, False otherwise
        """
        try:
            import pypdf

            return True
        except ImportError:
            return False

    def extract_metadata(self, file_path: str) -> dict[str, Any]:
        """Extract metadata from a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            Dictionary containing metadata

        Raises:
            ExtractorError: If metadata extraction fails
        """
        if not os.path.exists(file_path):
            raise ExtractorError(f"File not found: {file_path}")

        if not self._has_pypdf:
            # Limited metadata if pypdf is not available
            stat_info = os.stat(file_path)
            return {
                "file_type": "pdf",
                "extension": ".pdf",
                "size_bytes": stat_info.st_size,
                "last_modified": stat_info.st_mtime,
                "created": stat_info.st_ctime,
                "note": "Limited metadata: pypdf library not available",
            }

        try:
            import pypdf

            stat_info = os.stat(file_path)
            metadata = {
                "file_type": "pdf",
                "extension": ".pdf",
                "size_bytes": stat_info.st_size,
                "last_modified": stat_info.st_mtime,
                "created": stat_info.st_ctime,
            }

            with open(file_path, "rb") as file:
                reader = pypdf.PdfReader(file)

                # Number of pages
                metadata["page_count"] = len(reader.pages)

                # Document info from PDF metadata
                info = reader.metadata
                if info:
                    if info.title:
                        metadata["title"] = info.title
                    if info.author:
                        metadata["author"] = info.author
                    if info.subject:
                        metadata["subject"] = info.subject
                    if info.creator:
                        metadata["creator"] = info.creator
                    if info.producer:
                        metadata["producer"] = info.producer
                    if info.creation_date:
                        metadata["pdf_creation_date"] = info.creation_date
                    if info.modification_date:
                        metadata["pdf_modification_date"] = info.modification_date

            return metadata

        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {str(e)}")
            raise ExtractorError(
                f"Failed to extract metadata from {file_path}: {str(e)}"
            ) from e

    def extract_content(self, file_path: str) -> str:
        """Extract textual content from a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            Extracted textual content

        Raises:
            ExtractorError: If content extraction fails
        """
        if not os.path.exists(file_path):
            raise ExtractorError(f"File not found: {file_path}")

        if not self._has_pypdf:
            raise ExtractorError("PDF text extraction requires the pypdf library")

        try:
            import pypdf

            text = ""
            with open(file_path, "rb") as file:
                reader = pypdf.PdfReader(file)

                for page_num in range(len(reader.pages)):
                    text += reader.pages[page_num].extract_text() + "\n\n"

            return text

        except Exception as e:
            logger.error(f"Error extracting content from {file_path}: {str(e)}")
            raise ExtractorError(
                f"Failed to extract content from {file_path}: {str(e)}"
            ) from e

    def generate_preview(self, file_path: str, max_size: int = 1000) -> str:
        """Generate a textual preview of the PDF content.

        Args:
            file_path: Path to the PDF file
            max_size: Maximum size of the preview in characters

        Returns:
            A textual preview of the file content

        Raises:
            ExtractorError: If preview generation fails
        """
        if not os.path.exists(file_path):
            raise ExtractorError(f"File not found: {file_path}")

        if not self._has_pypdf:
            return f"[PDF file: {os.path.basename(file_path)}] - Install pypdf library for preview"

        try:
            import pypdf

            preview = ""
            with open(file_path, "rb") as file:
                reader = pypdf.PdfReader(file)

                # Extract metadata for the preview
                info = reader.metadata
                if info and info.title:
                    preview += f"Title: {info.title}\n"
                if info and info.author:
                    preview += f"Author: {info.author}\n"

                preview += f"Pages: {len(reader.pages)}\n\n"

                # Extract text from the first few pages until we reach max_size
                for page_num in range(min(3, len(reader.pages))):
                    page_text = reader.pages[page_num].extract_text()
                    preview += f"--- Page {page_num + 1} ---\n"
                    if len(preview) + len(page_text) > max_size:
                        preview += page_text[: max_size - len(preview) - 3] + "..."
                        break
                    preview += page_text + "\n\n"

            return preview

        except Exception as e:
            logger.error(f"Error generating preview for {file_path}: {str(e)}")
            raise ExtractorError(
                f"Failed to generate preview for {file_path}: {str(e)}"
            ) from e
