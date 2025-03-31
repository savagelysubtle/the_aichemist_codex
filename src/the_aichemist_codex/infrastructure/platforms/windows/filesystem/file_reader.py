"""
File Reader Module - Provides functionality for reading files with MIME type detection.
"""

import concurrent.futures
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import magic  # python-magic for MIME type detection
except ImportError:
    logging.warning("python-magic not installed. MIME type detection may be limited.")
    magic = None

from .file_metadata import FileMetadata


class FileReader:
    """Class for reading files with automatic MIME type detection."""

    def __init__(
        self,
        max_workers: int = 4,
        preview_length: int = 1000,
        cache_manager: Any = None,
    ):
        """
        Initialize the FileReader.

        Args:
            max_workers: Maximum number of worker threads for parallel processing
            preview_length: Number of characters to include in content preview
            cache_manager: Optional cache manager for caching results
        """
        self.max_workers = max_workers
        self.preview_length = preview_length
        self.cache_manager = cache_manager
        self.logger = logging.getLogger(__name__)

    def get_mime_type(self, file_path: str | Path) -> str:
        """
        Get MIME type of a file.

        Args:
            file_path: Path to the file

        Returns:
            MIME type string
        """
        file_path = Path(file_path)

        try:
            if magic:
                return magic.from_file(str(file_path), mime=True)
            else:
                return self._fallback_mime_type(file_path)
        except Exception as e:
            self.logger.error(f"Error detecting MIME type for {file_path}: {e}")
            return self._fallback_mime_type(file_path)

    def _fallback_mime_type(self, file_path: Path) -> str:
        """Fallback method for MIME type detection based on extension."""
        extension = file_path.suffix.lower()

        # Basic mapping of common extensions to MIME types
        mime_mapping = {
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".html": "text/html",
            ".htm": "text/html",
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".mp3": "audio/mpeg",
            ".mp4": "video/mp4",
            ".py": "text/x-python",
            ".js": "text/javascript",
            ".json": "application/json",
            ".xml": "application/xml",
            ".csv": "text/csv",
            ".zip": "application/zip",
        }

        return mime_mapping.get(extension, "application/octet-stream")

    def read_files(self, file_paths: list[str | Path]) -> list[FileMetadata]:
        """
        Read multiple files in parallel and return their metadata.

        Args:
            file_paths: List of file paths to process

        Returns:
            List of FileMetadata objects
        """
        results = []

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            future_to_file = {
                executor.submit(self.process_file, file_path): file_path
                for file_path in file_paths
            }

            for future in concurrent.futures.as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    metadata = future.result()
                    if metadata:
                        results.append(metadata)
                except Exception as e:
                    self.logger.error(f"Error processing {file_path}: {e}")

        return results

    def process_file(self, file_path: str | Path) -> FileMetadata | None:
        """
        Process a single file and return its metadata.

        Args:
            file_path: Path to the file

        Returns:
            FileMetadata object or None if processing fails
        """
        file_path = Path(file_path)

        if not file_path.exists():
            self.logger.warning(f"File not found: {file_path}")
            return None

        try:
            # Get basic file stats
            stats = file_path.stat()

            # Create metadata object
            metadata = FileMetadata(
                path=file_path,
                name=file_path.name,
                size=stats.st_size,
                mime_type=self.get_mime_type(file_path),
                extension=file_path.suffix,
                created_at=datetime.fromtimestamp(stats.st_ctime),
                modified_at=datetime.fromtimestamp(stats.st_mtime),
                accessed_at=datetime.fromtimestamp(stats.st_atime),
                is_hidden=file_path.name.startswith(".")
                or bool(os.stat(file_path).st_file_attributes & 0x2)
                if os.name == "nt"
                else False,
                is_system=bool(os.stat(file_path).st_file_attributes & 0x4)
                if os.name == "nt"
                else False,
                is_readonly=not os.access(file_path, os.W_OK),
            )

            # Read preview if it's a text file
            if metadata.mime_type.startswith("text/") or metadata.extension in [
                ".md",
                ".py",
                ".js",
                ".json",
                ".xml",
                ".csv",
            ]:
                try:
                    with open(file_path, encoding="utf-8", errors="replace") as f:
                        content = f.read(self.preview_length)
                        metadata.preview = content

                        # Calculate word count for text files
                        if metadata.mime_type.startswith("text/"):
                            metadata.word_count = len(content.split())
                except Exception as e:
                    self.logger.warning(f"Error reading preview for {file_path}: {e}")

            return metadata

        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}")
            return None
