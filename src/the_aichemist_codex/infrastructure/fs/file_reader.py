"""
File reading and parsing module for The Aichemist Codex.
This module provides functionality for reading and parsing various file types,
including text files, documents, spreadsheets, code files, and more.
"""

import asyncio
import logging
import warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Import python-magic safely
try:
    import magic
except ImportError:
    magic = None

# Import local modules
from .file_metadata import FileMetadata
from .parsers import get_parser_for_mime_type

logger = logging.getLogger(__name__)


class FileReader:
    """Main class for reading and parsing files with MIME type detection."""

    def __init__(
        self,
        max_workers: int = 2,
        preview_length: int = 100,
        cache_manager: object | None = None,
    ) -> None:
        """Initialize FileReader.

        Args:
            max_workers (int): Maximum number of worker threads for
                concurrent operations
            preview_length (int): Maximum length of file previews
            cache_manager (Optional[Any]): Cache manager for
                caching extraction results
        """
        self.max_workers = max_workers
        self.preview_length = preview_length
        self.logger = logging.getLogger(__name__)

        # Initialize the magic library for file type detection
        self._magic_instance = None

        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.cache_manager = cache_manager

    def get_mime_type(self, file_path: str | Path) -> str:
        """
        Get the MIME type of a file.

        Args:
            file_path: Path to the file

        Returns:
            str: MIME type of the file

        Raises:
            FileNotFoundError: If the file does not exist
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"{path} does not exist.")

        if magic is None:
            logger.warning("Magic library not available, using default MIME type")
            return "application/octet-stream"

        # Simple approach to handle the different implementations
        try:
            # Try direct function call (common in python-magic-bin)
            # Suppress errors from linter about from_file -
            #  we're handling this at runtime
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                from_file_attr = getattr(magic, "from_file", None)
                if callable(from_file_attr):
                    return from_file_attr(str(path), mime=True)
            # If we can't use from_file directly, try something else
            return self._fallback_mime_type(path)
        except Exception as e:
            logger.warning(f"Error determining MIME type: {e}")
            return self._fallback_mime_type(path)

    def _fallback_mime_type(self, path: Path) -> str:
        """Fallback method to detect MIME type based on file extension."""
        extension = path.suffix.lower()
        # Common MIME types based on file extensions
        mime_map = {
            ".txt": "text/plain",
            ".html": "text/html",
            ".htm": "text/html",
            ".css": "text/css",
            ".js": "application/javascript",
            ".json": "application/json",
            ".xml": "application/xml",
            ".csv": "text/csv",
            ".md": "text/markdown",
            ".py": "text/x-python",
            ".java": "text/x-java",
            ".rb": "text/x-ruby",
            ".php": "text/x-php",
            ".c": "text/x-c",
            ".cpp": "text/x-c++",
            ".h": "text/x-c-header",
            ".pdf": "application/pdf",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".mp3": "audio/mpeg",
            ".mp4": "video/mp4",
            ".zip": "application/zip",
            ".docx": (
                "application/vnd.openxmlformats-officedocument"
                ".wordprocessingml.document"
            ),
            ".xlsx": (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            ".pptx": (
                "application/vnd.openxmlformats-officedocument"
                ".presentationml.presentation"
            ),
        }
        return mime_map.get(extension, "application/octet-stream")

    def get_mime_types(self, file_paths: list[str | Path]) -> dict[str, str]:
        """
        Get MIME types for multiple files.

        Args:
            file_paths: List of file paths to process

        Returns:
            Dict[str, str]: Dictionary mapping file paths to their MIME types
        """
        return {str(path): self.get_mime_type(path) for path in file_paths}

    async def process_file(self, file_path: Path) -> FileMetadata:
        """
        Process a single file to extract its metadata and preview.

        Args:
            file_path: Path to the file to process

        Returns:
            FileMetadata: Metadata and preview information for the file
        """
        try:
            # Check if file exists
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Run MIME detection in thread pool to avoid blocking
            mime_type = await asyncio.get_event_loop().run_in_executor(
                self.executor, self.get_mime_type, file_path
            )

            metadata = FileMetadata(
                path=file_path,
                mime_type=mime_type,
                size=file_path.stat().st_size,
                extension=file_path.suffix.lower(),
                preview="",  # Will be filled in later
                error=None,
                parsed_data=None,
            )

            # Try to parse the file using the appropriate parser
            parser = get_parser_for_mime_type(mime_type)
            if parser:
                try:
                    parsed_data = await parser.parse(file_path)
                    preview = parser.get_preview(parsed_data, self.preview_length)
                    metadata.preview = preview
                    metadata.parsed_data = parsed_data
                except Exception as e:
                    metadata.error = f"Parsing failed: {str(e)}"
                    metadata.preview = f"[Error: {str(e)}]"
                    logger.warning(f"Failed to parse {file_path}: {e}")
            else:
                metadata.preview = f"[No parser available for {mime_type}]"

            return metadata

        except Exception as e:
            error_msg = f"Error processing file {file_path}: {str(e)}"
            logger.error(error_msg)
            return FileMetadata(
                path=file_path,
                mime_type="unknown",
                size=-1,
                extension=file_path.suffix.lower(),
                error=error_msg,
                preview="",
            )
