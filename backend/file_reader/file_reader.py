"""
File reading and parsing module for The Aichemist Codex.
This module provides functionality for reading and parsing various file types,
including text files, documents, spreadsheets, code files, and more.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import magic

from backend.config import settings

# Import the metadata manager
from backend.metadata.manager import MetadataManager
from backend.utils.async_io import AsyncFileIO
from backend.utils.cache_manager import CacheManager

from .file_metadata import FileMetadata
from .parsers import get_parser_for_mime_type

logger = logging.getLogger(__name__)


class FileReader:
    """Main class for reading and parsing files with MIME type detection."""

    def __init__(
        self,
        max_workers: int = 2,
        preview_length: int = 100,
        cache_manager: Optional[CacheManager] = None,
    ):
        """Initialize FileReader.

        Args:
            max_workers (int): Maximum number of worker threads for concurrent operations
            preview_length (int): Maximum length of file previews
            cache_manager (Optional[CacheManager]): Cache manager for caching extraction results
        """
        self.max_workers = max_workers
        self.preview_length = preview_length
        self.logger = logging.getLogger(__name__)
        self.mime = magic.Magic(mime=True)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.cache_manager = cache_manager

        # Initialize the metadata manager
        self.metadata_manager = MetadataManager(cache_manager)

    def get_mime_type(self, file_path: Union[str, Path]) -> str:
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
        return self.mime.from_file(str(path))

    def get_mime_types(self, file_paths: List[Union[str, Path]]) -> Dict[str, str]:
        """
        Get MIME types for multiple files.

        Args:
            file_paths: List of file paths to process

        Returns:
            Dict[str, str]: Dictionary mapping file paths to their MIME types
        """
        return {str(path): self.get_mime_type(path) for path in file_paths}

    async def read_files(self, file_paths: List[Path]) -> List[FileMetadata]:
        """Read multiple files and return their metadata.

        Args:
            file_paths (List[Path]): List of paths to read

        Returns:
            List[FileMetadata]: List of metadata for each file
        """
        results = []
        for path in file_paths:
            try:
                # Use AsyncFileIO to check for file existence.
                if not await AsyncFileIO.exists(path):
                    raise FileNotFoundError(f"Cannot find the file: {path}")

                stats = path.stat()
                size = stats.st_size
                mime_type = self.get_mime_type(path)

                # Generate preview for text files
                preview = ""
                if mime_type.startswith("text/"):
                    content = await AsyncFileIO.read(path)
                    if content.startswith("# "):  # Error message or skipped file
                        error_msg = content[2:]  # Remove "# " prefix
                        raise RuntimeError(error_msg)

                    preview = (
                        content[: self.preview_length] + "..."
                        if len(content) > self.preview_length
                        else content
                    )

                metadata = FileMetadata(
                    path=path,
                    mime_type=mime_type,
                    size=size,
                    extension=path.suffix,
                    preview=preview,
                    error=None,
                    parsed_data=None,
                )
                results.append(metadata)

            except Exception as e:
                # Handle errors gracefully
                error_msg = f"Error processing file {path}: {str(e)}"
                self.logger.error(error_msg)
                metadata = FileMetadata(
                    path=path,
                    mime_type="unknown",
                    size=-1,
                    extension=path.suffix if path else "",
                    preview="",
                    error=error_msg,
                    parsed_data=None,
                )
                results.append(metadata)

        return results

    async def process_file(self, file_path: Path) -> FileMetadata:
        """
        Process a single file to extract its metadata and preview.

        Args:
            file_path: Path to the file to process

        Returns:
            FileMetadata: Metadata and preview information for the file
        """
        try:
            # Use AsyncFileIO to check file existence.
            if not await AsyncFileIO.exists(file_path):
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
                preview="",  # Added preview parameter
                error=None,  # Added error parameter
                parsed_data=None,
            )

            # Get preview and basic parsed data if possible
            try:
                preview, parsed_data = await self._get_preview_and_data(
                    file_path, mime_type
                )
                metadata.preview = preview if preview else ""
                metadata.parsed_data = parsed_data
            except Exception as e:
                metadata.error = f"Preview generation failed: {str(e)}"
                metadata.preview = ""
                logger.warning(f"Failed to generate preview for {file_path}: {e}")

            # Extract enhanced metadata if the feature is enabled
            if (
                hasattr(settings, "ENABLE_ENHANCED_METADATA")
                and settings.ENABLE_ENHANCED_METADATA
            ):
                try:
                    # Get the file content if we don't have it already
                    content = None
                    if mime_type.startswith("text/"):
                        content = await AsyncFileIO.read(file_path)

                    # Extract enhanced metadata
                    enhanced_metadata = await self.metadata_manager.extract_metadata(
                        file_path=file_path,
                        content=content,
                        mime_type=mime_type,
                        metadata=metadata,
                    )

                    # Use the enhanced metadata
                    metadata = enhanced_metadata

                    logger.debug(f"Enhanced metadata extracted for {file_path}")
                except Exception as e:
                    logger.warning(
                        f"Enhanced metadata extraction failed for {file_path}: {e}"
                    )
                    # We still have the basic metadata, so continue

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

    async def _get_preview_and_data(
        self, file_path: Path, mime_type: str
    ) -> tuple[str, Optional[Dict[str, Any]]]:
        """
        Get a preview of the file contents and parsed data based on its MIME type.

        Args:
            file_path: Path to the file
            mime_type: MIME type of the file

        Returns:
            Tuple of (preview_string, parsed_data_dict)
        """
        parser = get_parser_for_mime_type(mime_type)

        if parser:
            try:
                parsed_data = await parser.parse(file_path)
                preview = parser.get_preview(parsed_data, self.preview_length)
                return preview, parsed_data
            except Exception as e:
                self.logger.warning(f"Parser failed for {file_path}: {e}")
                # Fall back to basic text preview if parser fails
                return await self._read_text_preview(file_path), None

        # For unsupported file types, return a basic message
        return f"[Binary file of type: {mime_type}]", None

    async def _read_text_preview(self, file_path: Path) -> str:
        """Read a text preview of a file.

        Args:
            file_path: Path to the file

        Returns:
            A string preview of the file content
        """
        try:
            content = await AsyncFileIO.read(file_path)
            if content.startswith("# "):  # Error message or skipped file
                return f"[Preview error: {content[2:]}]"

            return (
                content[: self.preview_length] + "..."
                if len(content) > self.preview_length
                else content
            )
        except Exception as e:
            self.logger.error(f"Error reading text preview from {file_path}: {e}")
            return f"[Error reading preview: {e}]"
