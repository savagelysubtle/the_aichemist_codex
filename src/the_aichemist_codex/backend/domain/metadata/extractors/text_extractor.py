import logging
import os
from typing import Any

from ....core.exceptions import ExtractorError
from ..extractor import Extractor

logger = logging.getLogger(__name__)


class TextExtractor(Extractor):
    """Extractor for text files."""

    def __init__(self):
        super().__init__()
        self._supported_extensions = {
            ".txt",
            ".csv",
            ".md",
            ".log",
            ".json",
            ".yaml",
            ".yml",
            ".xml",
            ".html",
            ".htm",
            ".css",
            ".js",
            ".ts",
            ".py",
            ".java",
            ".c",
            ".cpp",
            ".h",
            ".cs",
            ".go",
            ".rs",
            ".php",
            ".rb",
            ".pl",
            ".sh",
            ".bat",
            ".ps1",
            ".sql",
        }
        self._supported_mime_types = {
            "text/plain",
            "text/csv",
            "text/markdown",
            "text/html",
            "text/css",
            "text/javascript",
            "application/json",
            "application/xml",
            "application/x-yaml",
        }

    def extract_metadata(self, file_path: str) -> dict[str, Any]:
        """Extract metadata from a text file.

        Args:
            file_path: Path to the text file

        Returns:
            Dictionary containing metadata

        Raises:
            ExtractorError: If metadata extraction fails
        """
        if not os.path.exists(file_path):
            raise ExtractorError(f"File not found: {file_path}")

        try:
            stat_info = os.stat(file_path)

            # Get file extension and language
            _, ext = os.path.splitext(file_path)
            language = self._determine_language(ext)

            # Basic metadata
            metadata = {
                "file_type": "text",
                "extension": ext.lower(),
                "language": language,
                "size_bytes": stat_info.st_size,
                "last_modified": stat_info.st_mtime,
                "created": stat_info.st_ctime,
                "line_count": 0,
                "word_count": 0,
                "char_count": 0,
            }

            # Calculate content statistics
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                    lines = content.splitlines()
                    words = content.split()

                    metadata["line_count"] = len(lines)
                    metadata["word_count"] = len(words)
                    metadata["char_count"] = len(content)
            except UnicodeDecodeError:
                # File might not be UTF-8 encoded
                logger.warning(f"Could not read {file_path} as UTF-8 text")

            return metadata

        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {str(e)}")
            raise ExtractorError(
                f"Failed to extract metadata from {file_path}: {str(e)}"
            ) from e

    def extract_content(self, file_path: str) -> str:
        """Extract textual content from a text file.

        Args:
            file_path: Path to the text file

        Returns:
            Extracted textual content

        Raises:
            ExtractorError: If content extraction fails
        """
        if not os.path.exists(file_path):
            raise ExtractorError(f"File not found: {file_path}")

        try:
            with open(file_path, encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                # Try with a different encoding
                with open(file_path, encoding="latin-1") as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error extracting content from {file_path}: {str(e)}")
                raise ExtractorError(
                    f"Failed to extract content from {file_path}: {str(e)}"
                ) from e
        except Exception as e:
            logger.error(f"Error extracting content from {file_path}: {str(e)}")
            raise ExtractorError(
                f"Failed to extract content from {file_path}: {str(e)}"
            ) from e
