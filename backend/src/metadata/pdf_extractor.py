"""
PDF metadata and content extraction for The Aichemist Codex.

This module provides functionality to extract metadata and content from PDF files,
including document properties, text content, page count, layout information, and
other PDF-specific metadata.
"""

import logging
from pathlib import Path
from typing import Any, cast

# Third-party imports
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError

try:
    import pdf2image

    PDF2IMAGE_AVAILABLE = True
except ImportError:
    # pdf2image is optional - we'll still provide basic functionality without it
    PDF2IMAGE_AVAILABLE = False

# Local application imports
from backend.src.file_reader.file_metadata import FileMetadata
from backend.src.metadata.extractor import (
    BaseMetadataExtractor,
    MetadataExtractorRegistry,
)
from backend.src.utils.cache_manager import CacheManager
from backend.src.utils.mime_type_detector import MimeTypeDetector

# Initialize logger with proper name
logger = logging.getLogger(__name__)

# Define PyPDF2 types for better type checking
PdfDict = dict[str, Any]
PdfObject = Any  # PyPDF2 doesn't have clear type hints for all objects


class PDFMetadataExtractor(BaseMetadataExtractor):
    """
    Metadata and content extractor for PDF files.

    This extractor can process PDF files and extract rich metadata including:
    - Document properties (title, author, creation date, etc.)
    - Page count and dimensions
    - Text content and structure
    - Font information
    - Embedded images (count and types)
    - Security and encryption status
    - PDF version
    """

    # Supported MIME types
    SUPPORTED_MIME_TYPES = [
        "application/pdf",
        "application/x-pdf",
        "application/acrobat",
        "application/vnd.pdf",
    ]

    # Maximum text extraction size (bytes) to prevent excessive memory usage
    MAX_TEXT_EXTRACTION_SIZE = 10 * 1024 * 1024  # 10MB

    # Maximum number of pages to extract text from for large documents
    MAX_PAGES_FULL_EXTRACT = 50

    @property
    def supported_mime_types(self) -> list[str]:
        """Get the list of MIME types this extractor supports.

        Returns:
            List of supported MIME types
        """
        return self.SUPPORTED_MIME_TYPES

    def __init__(self, cache_manager: CacheManager | None = None) -> None:
        """Initialize the PDF metadata extractor.

        Args:
            cache_manager: Optional cache manager for caching extraction results
        """
        super().__init__(cache_manager)
        self.mime_detector = MimeTypeDetector()

    async def extract(
        self,
        file_path: str | Path,
        content: str | None = None,
        mime_type: str | None = None,
        metadata: FileMetadata | None = None,
    ) -> dict[str, Any]:
        """Extract metadata and content from a PDF file.

        Args:
            file_path: Path to the PDF file
            content: Not used for PDF files
            mime_type: Optional MIME type of the file
            metadata: Optional existing metadata to enhance

        Returns:
            Dictionary containing extracted PDF metadata and content
        """
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"PDF file not found: {path}")
            return {}

        # Determine MIME type if not provided
        if mime_type is None:
            mime_type, _ = self.mime_detector.get_mime_type(path)

        # Check if this is a supported PDF type
        if mime_type not in self.supported_mime_types:
            logger.debug(f"Unsupported MIME type for PDF: {mime_type} for file: {path}")
            return {}

        # Try to use cache if available
        if self.cache_manager:
            cache_key = f"pdf_metadata:{path}:{path.stat().st_mtime}"
            cached_data = await self.cache_manager.get(cache_key)
            if cached_data:
                logger.debug(f"Using cached PDF metadata for {path}")
                return cached_data

        # Process the PDF file
        try:
            result = await self._process_pdf(path)

            # Cache the result if cache manager is available
            if self.cache_manager:
                await self.cache_manager.put(cache_key, result)

            return result
        except Exception as e:
            logger.error(f"Error extracting PDF metadata from {path}: {str(e)}")
            return {
                "metadata_type": "pdf",
                "error": f"Error extracting PDF metadata: {str(e)}",
            }

    async def _process_pdf(self, path: Path) -> dict[str, Any]:
        """Process a PDF file to extract metadata and content.

        Args:
            path: Path to the PDF file

        Returns:
            Dictionary containing extracted PDF metadata and content
        """
        result = {
            "metadata_type": "pdf",
            "document": {},
            "content": {},
            "structure": {},
            "security": {},
        }

        # Basic file information
        result["document"]["file_size"] = path.stat().st_size

        try:
            # Open the PDF file
            with open(path, "rb") as file:
                # Check if file is too large for full processing
                is_large_file = path.stat().st_size > self.MAX_TEXT_EXTRACTION_SIZE

                try:
                    # Create PDF reader
                    pdf = PdfReader(file)

                    # Extract basic document information
                    self._extract_document_info(pdf, result)

                    # Extract page information
                    self._extract_page_info(pdf, result)

                    # Extract text content (with limits for large files)
                    self._extract_text_content(pdf, result, is_large_file)

                    # Extract font information
                    self._extract_font_info(pdf, result)

                    # Extract image information
                    self._extract_image_info(pdf, result)

                    # Extract security information
                    self._extract_security_info(pdf, result)

                    # Add summary
                    page_count = result["structure"]["page_count"]
                    page_text = "page" if page_count == 1 else "pages"

                    title = result["document"].get("title", "Untitled")
                    author = result["document"].get("author", "Unknown author")

                    result["summary"] = (
                        f"PDF document '{title}' by {author} with {page_count} {page_text}"
                    )

                except PdfReadError as e:
                    # Handle corrupted PDF files
                    logger.warning(f"Error reading PDF file {path}: {str(e)}")
                    result["error"] = f"Error reading PDF: {str(e)}"

        except Exception as e:
            logger.error(f"Error processing PDF file {path}: {str(e)}")
            result["error"] = f"Error processing PDF: {str(e)}"

        return result

    def _extract_document_info(self, pdf: PdfReader, result: dict[str, Any]) -> None:
        """Extract document information from the PDF.

        Args:
            pdf: PyPDF2 PDF reader object
            result: Dictionary to update with extracted information
        """
        # Extract document metadata
        if pdf.metadata:
            # Map PyPDF2 metadata keys to our standardized keys
            metadata_mapping = {
                "/Title": "title",
                "/Author": "author",
                "/Subject": "subject",
                "/Keywords": "keywords",
                "/Creator": "creator",
                "/Producer": "producer",
                "/CreationDate": "creation_date",
                "/ModDate": "modification_date",
            }

            for pdf_key, our_key in metadata_mapping.items():
                if pdf_key in pdf.metadata:
                    value = pdf.metadata[pdf_key]
                    # Clean up date strings
                    if isinstance(value, str) and pdf_key in [
                        "/CreationDate",
                        "/ModDate",
                    ]:
                        # PDF dates format: D:YYYYMMDDHHmmSS
                        if value.startswith("D:"):
                            try:
                                # Extract the date portion and format it
                                date_str = value[2:14]  # Extract YYYYMMDDHHMM
                                formatted_date = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]} {date_str[8:10]}:{date_str[10:12]}"
                                value = formatted_date
                            except Exception:
                                # If parsing fails, keep original
                                pass
                    result["document"][our_key] = value

        # Extract PDF version
        if hasattr(pdf, "pdf_header"):
            result["document"]["pdf_version"] = pdf.pdf_header

    def _extract_page_info(self, pdf: PdfReader, result: dict[str, Any]) -> None:
        """Extract page information from the PDF.

        Args:
            pdf: PyPDF2 PDF reader object
            result: Dictionary to update with extracted information
        """
        # Get page count
        page_count = len(pdf.pages)
        result["structure"]["page_count"] = page_count

        # Extract information about pages
        pages_info = []

        # Limit page info extraction for very large documents
        max_pages_to_analyze = min(page_count, 100)  # Analyze at most 100 pages

        for i in range(max_pages_to_analyze):
            page = pdf.pages[i]
            page_info = {
                "page_number": i + 1,
                "width": float(page.mediabox.width),
                "height": float(page.mediabox.height),
                "rotation": page.get("/Rotate", 0),
            }

            # Add page dimensions in points (1/72 inch)
            page_info["size_points"] = f"{page_info['width']} x {page_info['height']}"

            # Calculate approximate size in inches and mm
            width_inch = page_info["width"] / 72
            height_inch = page_info["height"] / 72
            width_mm = width_inch * 25.4
            height_mm = height_inch * 25.4

            page_info["size_inches"] = f"{width_inch:.2f} x {height_inch:.2f}"
            page_info["size_mm"] = f"{width_mm:.2f} x {height_mm:.2f}"

            # Try to determine page size standard
            # Standard page sizes in points (width, height)
            standard_sizes = {
                "A4": (595, 842),
                "A3": (842, 1191),
                "Letter": (612, 792),
                "Legal": (612, 1008),
                "Tabloid": (792, 1224),
            }

            # Check if page matches a standard size (within 2 points tolerance)
            for size_name, (std_w, std_h) in standard_sizes.items():
                w_diff = abs(page_info["width"] - std_w)
                h_diff = abs(page_info["height"] - std_h)
                rotated_w_diff = abs(page_info["width"] - std_h)
                rotated_h_diff = abs(page_info["height"] - std_w)

                if (w_diff <= 2 and h_diff <= 2) or (
                    rotated_w_diff <= 2 and rotated_h_diff <= 2
                ):
                    page_info["standard_size"] = size_name
                    break

            pages_info.append(page_info)

        # Add page info to result
        result["structure"]["pages"] = pages_info

        # Determine if all pages have the same size
        if page_count > 0:
            sizes = set()
            for page in pages_info:
                sizes.add((page["width"], page["height"]))

            result["structure"]["uniform_page_size"] = len(sizes) == 1

            # Get the most common page size
            if result["structure"]["uniform_page_size"]:
                width, height = next(iter(sizes))
                result["structure"]["page_size"] = {
                    "width": width,
                    "height": height,
                }

                # Add standard size if available
                if "standard_size" in pages_info[0]:
                    result["structure"]["standard_size"] = pages_info[0][
                        "standard_size"
                    ]

    def _extract_text_content(
        self, pdf: PdfReader, result: dict[str, Any], is_large_file: bool
    ) -> None:
        """Extract text content from the PDF.

        Args:
            pdf: PyPDF2 PDF reader object
            result: Dictionary to update with extracted information
            is_large_file: Whether the file is considered large
        """
        page_count = len(pdf.pages)

        # Determine how many pages to extract
        pages_to_extract = page_count
        if is_large_file:
            pages_to_extract = min(page_count, self.MAX_PAGES_FULL_EXTRACT)
            result["content"]["text_extraction_limited"] = True
            result["content"]["text_extraction_page_limit"] = (
                self.MAX_PAGES_FULL_EXTRACT
            )

        # Extract text from each page
        all_text = []
        page_text = []

        for i in range(pages_to_extract):
            try:
                text = pdf.pages[i].extract_text()
                all_text.append(text)

                # Store individual page text (with reasonable limits)
                if len(page_text) < 20:  # Store text for at most 20 pages
                    page_text.append(
                        {
                            "page_number": i + 1,
                            "text": text[:1000]
                            if len(text) > 1000
                            else text,  # Limit to 1000 chars per page
                            "character_count": len(text),
                        }
                    )
            except Exception as e:
                logger.warning(f"Error extracting text from page {i + 1}: {str(e)}")
                # Add placeholder
                all_text.append("")
                if len(page_text) < 20:
                    page_text.append(
                        {
                            "page_number": i + 1,
                            "text": f"[Error extracting text: {str(e)}]",
                            "character_count": 0,
                        }
                    )

        # Calculate stats on extracted text
        full_text = "\n\n".join(all_text)
        char_count = len(full_text)

        # Word count (approximate)
        words = full_text.split()
        word_count = len(words)

        # Calculate average word length
        avg_word_len = sum(len(w) for w in words) / max(1, word_count)

        # Calculate line count (approximate)
        line_count = full_text.count("\n") + 1

        # Store content information
        result["content"]["character_count"] = char_count
        result["content"]["word_count"] = word_count
        result["content"]["line_count"] = line_count
        result["content"]["average_word_length"] = round(avg_word_len, 2)
        result["content"]["page_text"] = page_text

        # Only store full text if it's not too large
        if char_count <= 100000:  # Limit to 100KB of text
            result["content"]["full_text"] = full_text
        else:
            # Store just the beginning and end
            beginning = full_text[:25000]  # First ~25KB
            ending = full_text[-25000:]  # Last ~25KB
            result["content"]["text_excerpt"] = {
                "beginning": beginning,
                "ending": ending,
                "note": "Full text is too large to include in metadata",
            }

        # Check if document appears to be scanned
        result["content"]["appears_scanned"] = self._check_if_scanned(pdf, all_text)

    def _extract_font_info(self, pdf: PdfReader, result: dict[str, Any]) -> None:
        """Extract font information from the PDF.

        Args:
            pdf: PyPDF2 PDF reader object
            result: Dictionary to update with extracted information
        """
        # Initialize font tracking
        fonts: set[str] = set()
        page_count = len(pdf.pages)

        # Limit analysis to first 20 pages for performance
        max_pages = min(page_count, 20)

        for i in range(max_pages):
            page = pdf.pages[i]

            # Try to extract font information from the page resources
            # Use safer dictionary access to avoid type checking errors
            try:
                page_obj = cast(dict[str, Any], page)
                resources = page_obj.get("/Resources", {})
                if isinstance(resources, dict) and "/Font" in resources:
                    font_dict = resources["/Font"]
                    if isinstance(font_dict, dict):
                        for font in font_dict.values():
                            if isinstance(font, dict) and "/BaseFont" in font:
                                font_name = font["/BaseFont"]
                                if isinstance(font_name, str):
                                    # Clean up font name
                                    if font_name.startswith("/"):
                                        font_name = font_name[1:]
                                    fonts.add(font_name)
            except Exception as e:
                logger.debug(f"Error extracting font info from page {i + 1}: {str(e)}")
                continue

        # Store font information
        result["structure"]["fonts"] = sorted(list(fonts))
        result["structure"]["font_count"] = len(fonts)

    def _extract_image_info(self, pdf: PdfReader, result: dict[str, Any]) -> None:
        """Extract image information from the PDF.

        Args:
            pdf: PyPDF2 PDF reader object
            result: Dictionary to update with extracted information
        """
        # Initialize image tracking
        image_count = 0
        page_count = len(pdf.pages)

        # Limit analysis to first 20 pages for performance
        max_pages = min(page_count, 20)
        has_images = False

        for i in range(max_pages):
            page = pdf.pages[i]

            # Try to detect images in the page resources
            # Use safer dictionary access to avoid type checking errors
            try:
                page_obj = cast(dict[str, Any], page)
                resources = page_obj.get("/Resources", {})
                if isinstance(resources, dict) and "/XObject" in resources:
                    xobject_dict = resources["/XObject"]
                    if isinstance(xobject_dict, dict):
                        for obj in xobject_dict.values():
                            if (
                                isinstance(obj, dict)
                                and obj.get("/Subtype") == "/Image"
                            ):
                                image_count += 1
                                has_images = True
            except Exception as e:
                logger.debug(f"Error extracting image info from page {i + 1}: {str(e)}")
                continue

        # Store image information
        result["structure"]["has_images"] = has_images
        result["structure"]["image_count_sampled"] = image_count

        # Note that image count is from a sample of pages
        if page_count > max_pages:
            result["structure"]["image_count_estimated"] = int(
                image_count * (page_count / max_pages)
            )
            result["structure"]["image_count_note"] = (
                f"Image count estimated from first {max_pages} pages"
            )

        # Check for image extraction capability
        result["structure"]["image_extraction_supported"] = PDF2IMAGE_AVAILABLE

    def _extract_security_info(self, pdf: PdfReader, result: dict[str, Any]) -> None:
        """Extract security information from the PDF.

        Args:
            pdf: PyPDF2 PDF reader object
            result: Dictionary to update with extracted information
        """
        # Check if document is encrypted
        is_encrypted = pdf.is_encrypted
        result["security"]["encrypted"] = is_encrypted

        if is_encrypted:
            # Try to determine encryption method and permissions
            result["security"]["encryption_method"] = "Standard"  # Default

            # Handle permissions in a PyPDF2 version-independent way
            try:
                permissions = []

                # PyPDF2 has changed its permission API across versions
                # Instead of calling get_permissions() directly, we'll check for common
                # permission attributes that might be available
                permission_attributes = [
                    "can_print",
                    "can_modify",
                    "can_copy",
                    "can_annotate",
                    "can_fill_forms",
                    "can_extract",
                    "can_assemble",
                    "can_print_high_quality",
                ]

                # Map permission attribute names to readable descriptions
                perm_map = {
                    "can_print": "Printing",
                    "can_modify": "Modifying content",
                    "can_copy": "Copying content",
                    "can_annotate": "Annotating",
                    "can_fill_forms": "Filling forms",
                    "can_assemble": "Document assembly",
                    "can_print_high_quality": "High-quality printing",
                    "can_extract": "Content extraction",
                }

                # Check for permissions directly on the pdf object
                for attr in permission_attributes:
                    if hasattr(pdf, attr):
                        try:
                            if getattr(pdf, attr):
                                permissions.append(perm_map.get(attr, attr))
                        except Exception:
                            pass

                # If we found any permissions, store them
                if permissions:
                    result["security"]["permissions"] = permissions
                    result["security"]["has_restrictions"] = len(permissions) < len(
                        perm_map
                    )
                else:
                    result["security"]["permissions_note"] = (
                        "Unable to determine exact permissions"
                    )

                # Check for security info with safe attribute access
                if hasattr(pdf, "_security"):
                    security = getattr(pdf, "_security", None)
                    if security is not None:
                        if hasattr(security, "_owner_password_required"):
                            result["security"]["owner_password_protected"] = (
                                security._owner_password_required
                            )
                        if hasattr(security, "_user_password_required"):
                            result["security"]["user_password_protected"] = (
                                security._user_password_required
                            )
            except Exception as e:
                logger.debug(f"Error extracting security permissions: {str(e)}")
                result["security"]["permissions_note"] = "Error determining permissions"

    def _check_if_scanned(self, pdf: PdfReader, text_list: list[str]) -> bool:
        """Check if the PDF appears to be a scanned document.

        Args:
            pdf: PyPDF2 PDF reader object
            text_list: List of extracted text from each page

        Returns:
            Boolean indicating if the document appears to be scanned
        """
        # If there are images but very little text, it might be scanned
        has_images = False

        # Check a few pages for images
        pages_to_check = min(5, len(pdf.pages))
        for i in range(pages_to_check):
            page = pdf.pages[i]

            # Try to detect images, with safer dictionary access
            try:
                page_obj = cast(dict[str, Any], page)
                resources = page_obj.get("/Resources", {})
                if isinstance(resources, dict) and "/XObject" in resources:
                    xobject_dict = resources["/XObject"]
                    if isinstance(xobject_dict, dict):
                        for obj in xobject_dict.values():
                            if (
                                isinstance(obj, dict)
                                and obj.get("/Subtype") == "/Image"
                            ):
                                has_images = True
                                break
            except Exception:
                continue

            if has_images:
                break

        # Check if text extraction yielded reasonable results
        text_content = "".join(text_list[:pages_to_check])
        avg_text_per_page = len(text_content) / max(1, pages_to_check)

        # Heuristic: If there are images but very little text per page, it might be scanned
        # Typical scanned documents might have some OCR errors but still some text
        is_likely_scanned = has_images and avg_text_per_page < 100

        return is_likely_scanned


# Register the extractor
MetadataExtractorRegistry.register(PDFMetadataExtractor)
