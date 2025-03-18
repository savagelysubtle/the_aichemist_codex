import logging
import os
from typing import Any

from ....core.exceptions import ExtractorError
from ..extractor import Extractor

logger = logging.getLogger(__name__)


class ImageExtractor(Extractor):
    """Extractor for image files."""

    def __init__(self):
        super().__init__()
        self._supported_extensions = {
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".tiff",
            ".webp",
            ".svg",
            ".ico",
            ".heic",
            ".heif",
        }
        self._supported_mime_types = {
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/bmp",
            "image/tiff",
            "image/webp",
            "image/svg+xml",
            "image/x-icon",
            "image/heic",
            "image/heif",
        }

        # Check if required libraries are available
        self._has_pillow = self._check_pillow()
        if not self._has_pillow:
            logger.warning(
                "Pillow library not found. Image metadata extraction will be limited."
            )

    def _check_pillow(self) -> bool:
        """Check if Pillow library is available.

        Returns:
            True if the library is available, False otherwise
        """
        try:
            from PIL import Image

            return True
        except ImportError:
            return False

    def extract_metadata(self, file_path: str) -> dict[str, Any]:
        """Extract metadata from an image file.

        Args:
            file_path: Path to the image file

        Returns:
            Dictionary containing metadata

        Raises:
            ExtractorError: If metadata extraction fails
        """
        if not os.path.exists(file_path):
            raise ExtractorError(f"File not found: {file_path}")

        try:
            # Basic file info
            stat_info = os.stat(file_path)
            _, ext = os.path.splitext(file_path)

            metadata = {
                "file_type": "image",
                "extension": ext.lower(),
                "size_bytes": stat_info.st_size,
                "last_modified": stat_info.st_mtime,
                "created": stat_info.st_ctime,
            }

            # Enhanced metadata with Pillow if available
            if self._has_pillow:
                try:
                    from PIL import Image
                    from PIL.ExifTags import TAGS

                    with Image.open(file_path) as img:
                        # Basic image properties
                        metadata["width"] = img.width
                        metadata["height"] = img.height
                        metadata["format"] = img.format
                        metadata["mode"] = img.mode

                        # EXIF data if available
                        exif_data = {}
                        if hasattr(img, "_getexif") and img._getexif():
                            exif_info = img._getexif()
                            if exif_info:
                                for tag, value in exif_info.items():
                                    decoded = TAGS.get(tag, tag)
                                    # Convert bytes to strings when possible
                                    if isinstance(value, bytes):
                                        try:
                                            value = value.decode("utf-8")
                                        except UnicodeDecodeError:
                                            value = str(value)
                                    exif_data[decoded] = value

                                metadata["exif"] = exif_data

                                # Extract common EXIF fields
                                if "DateTimeOriginal" in exif_data:
                                    metadata["date_taken"] = exif_data[
                                        "DateTimeOriginal"
                                    ]
                                if "Make" in exif_data:
                                    metadata["camera_make"] = exif_data["Make"]
                                if "Model" in exif_data:
                                    metadata["camera_model"] = exif_data["Model"]
                except Exception as e:
                    logger.warning(f"Error extracting EXIF data: {str(e)}")

            return metadata

        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {str(e)}")
            raise ExtractorError(
                f"Failed to extract metadata from {file_path}: {str(e)}"
            ) from e

    def extract_content(self, file_path: str) -> str:
        """Extract textual content from an image file.

        For images, this attempts OCR if available, otherwise returns a description.

        Args:
            file_path: Path to the image file

        Returns:
            Extracted textual content or description

        Raises:
            ExtractorError: If content extraction fails
        """
        if not os.path.exists(file_path):
            raise ExtractorError(f"File not found: {file_path}")

        try:
            # First try to use OCR if pytesseract is available
            try:
                import pytesseract
                from PIL import Image

                with Image.open(file_path) as img:
                    text = pytesseract.image_to_string(img)
                    if text.strip():
                        return text
            except ImportError:
                logger.debug("pytesseract not available for OCR")
            except Exception as e:
                logger.warning(f"OCR failed: {str(e)}")

            # If OCR failed or isn't available, return image description
            metadata = self.extract_metadata(file_path)

            description = f"[Image: {os.path.basename(file_path)}]\n"
            if "width" in metadata and "height" in metadata:
                description += (
                    f"Dimensions: {metadata['width']}x{metadata['height']} pixels\n"
                )
            if "format" in metadata:
                description += f"Format: {metadata['format']}\n"
            if "camera_make" in metadata and "camera_model" in metadata:
                description += (
                    f"Camera: {metadata['camera_make']} {metadata['camera_model']}\n"
                )
            if "date_taken" in metadata:
                description += f"Date taken: {metadata['date_taken']}\n"

            return description

        except Exception as e:
            logger.error(f"Error extracting content from {file_path}: {str(e)}")
            raise ExtractorError(
                f"Failed to extract content from {file_path}: {str(e)}"
            ) from e

    def generate_preview(self, file_path: str, max_size: int = 1000) -> str:
        """Generate a textual preview of the image.

        Args:
            file_path: Path to the image file
            max_size: Maximum size of the preview in characters

        Returns:
            A textual description of the image

        Raises:
            ExtractorError: If preview generation fails
        """
        try:
            # For images, we just provide a description
            metadata = self.extract_metadata(file_path)

            preview = f"[Image: {os.path.basename(file_path)}]\n"
            if "width" in metadata and "height" in metadata:
                preview += (
                    f"Dimensions: {metadata['width']}x{metadata['height']} pixels\n"
                )
            if "format" in metadata:
                preview += f"Format: {metadata['format']}\n"
            if "camera_make" in metadata and "camera_model" in metadata:
                preview += (
                    f"Camera: {metadata['camera_make']} {metadata['camera_model']}\n"
                )
            if "date_taken" in metadata:
                preview += f"Date taken: {metadata['date_taken']}\n"

            # Add OCR text if possible
            try:
                import pytesseract
                from PIL import Image

                with Image.open(file_path) as img:
                    ocr_text = pytesseract.image_to_string(img)
                    if ocr_text.strip():
                        preview += "\nText content (OCR):\n"
                        if len(ocr_text) > max_size - len(preview):
                            preview += ocr_text[: max_size - len(preview) - 3] + "..."
                        else:
                            preview += ocr_text
            except (ImportError, Exception):
                pass

            return preview

        except Exception as e:
            logger.error(f"Error generating preview for {file_path}: {str(e)}")
            raise ExtractorError(
                f"Failed to generate preview for {file_path}: {str(e)}"
            ) from e
