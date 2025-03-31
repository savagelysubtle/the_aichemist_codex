"""Metadata extraction manager.

This module provides a central manager for coordinating metadata extraction
across different file types using appropriate extractors.
"""

import asyncio
import logging
import time
from pathlib import Path

from the_aichemist_codex.infrastructure.extraction.base_extractor import (
    BaseMetadataExtractor,
    MetadataExtractorRegistry,
)
from the_aichemist_codex.infrastructure.extraction.mime_detector import MimeTypeDetector
from the_aichemist_codex.infrastructure.fs.file_metadata import FileMetadata
from the_aichemist_codex.infrastructure.utils.cache.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class MetadataManager:
    """Manager for coordinating metadata extraction.

    This class orchestrates the extraction of metadata from files using
    the appropriate extractors based on file type.
    """

    def __init__(self, cache_manager: CacheManager | None = None):
        """Initialize the metadata manager.

        Args:
            cache_manager: Optional cache manager for caching extraction results
        """
        self.cache_manager = cache_manager
        self.mime_detector = MimeTypeDetector()

        # Initialize all available extractors
        self.extractors: dict[str, BaseMetadataExtractor] = {}
        for extractor_class in MetadataExtractorRegistry.get_all_extractors():
            extractor = extractor_class(cache_manager)
            for mime_type in extractor.supported_mime_types:
                self.extractors[mime_type] = extractor

    async def extract_metadata(
        self,
        file_path: str | Path,
        content: str | None = None,
        mime_type: str | None = None,
        metadata: FileMetadata | None = None,
    ) -> FileMetadata:
        """
        Extract metadata from a file.

        Args:
            file_path: Path to the file
            content: Optional pre-loaded content
            mime_type: Optional pre-determined MIME type
            metadata: Optional existing metadata to enhance

        Returns:
            Enhanced metadata with extracted information
        """
        path = Path(file_path) if isinstance(file_path, str) else file_path

        # If no metadata provided, create a basic one
        if metadata is None:
            try:
                if path.exists():
                    stats = path.stat()
                    size = stats.st_size
                    if mime_type is None:
                        mime_type, _ = self.mime_detector.get_mime_type(path)
                    extension = path.suffix.lower()
                else:
                    size = -1
                    if mime_type is None:
                        mime_type = "unknown"
                    extension = path.suffix.lower() if path.suffix else ""

                metadata = FileMetadata(
                    path=path,
                    mime_type=mime_type,
                    size=size,
                    extension=extension,
                    preview="",
                    error=None,
                    parsed_data=None,
                )
            except Exception as e:
                error_msg = f"Error creating metadata for {path}: {str(e)}"
                logger.error(error_msg)
                metadata = FileMetadata(
                    path=path,
                    mime_type="unknown",
                    size=-1,
                    extension=path.suffix.lower() if path.suffix else "",
                    preview="",
                    error=error_msg,
                    parsed_data=None,
                )

        # If MIME type not provided or in metadata, detect it
        if mime_type is None:
            mime_type = metadata.mime_type
            if mime_type is None or mime_type == "unknown":
                try:
                    if path.exists():
                        mime_type, _ = self.mime_detector.get_mime_type(path)
                        metadata.mime_type = mime_type
                except Exception as e:
                    logger.warning(f"Error detecting MIME type for {path}: {e}")

        # Check if we have an extractor for this MIME type
        extractors = self._get_extractors_for_mime_type(mime_type)

        if not extractors:
            logger.debug(f"No extractors found for MIME type: {mime_type}")
            return metadata

        # Apply each extractor in sequence
        for extractor in extractors:
            try:
                # Check cache first if available
                cache_key = None
                cached_metadata = None

                if self.cache_manager:
                    # Use file path and modification time as cache key
                    try:
                        mtime = path.stat().st_mtime if path.exists() else 0
                        cache_key = f"metadata:{str(path)}:{mtime}:{extractor.__class__.__name__}"
                        cached_metadata = self.cache_manager.memory_cache.get(cache_key)
                        if cached_metadata:
                            logger.debug(f"Using cached metadata for {path}")
                            # Update the existing metadata with cached values
                            for key, value in cached_metadata.items():
                                setattr(metadata, key, value)
                            continue
                    except Exception as e:
                        logger.warning(f"Error accessing cache for {path}: {e}")

                # Extract metadata
                start_time = time.time()
                extracted_data = await extractor.extract(
                    file_path=path,
                    content=content,
                    mime_type=mime_type,
                    metadata=metadata,
                )
                end_time = time.time()

                # Update the metadata
                for key, value in extracted_data.items():
                    if hasattr(metadata, key) and getattr(metadata, key) is None:
                        setattr(metadata, key, value)
                    elif not hasattr(metadata, key):
                        setattr(metadata, key, value)

                # Set extraction metadata
                metadata.extraction_complete = True
                metadata.extraction_time = end_time - start_time

                # Cache the result if caching is enabled
                if self.cache_manager and cache_key:
                    # Store a dictionary of the metadata attributes that were updated
                    cache_data = {key: value for key, value in extracted_data.items()}
                    self.cache_manager.memory_cache.put(cache_key, cache_data)

                logger.debug(
                    f"Metadata extraction completed in {metadata.extraction_time:.2f}s "
                    f"for {path} using {extractor.__class__.__name__}"
                )

            except Exception as e:
                error_msg = f"Error extracting metadata for {path}: {e}"
                logger.error(error_msg)
                metadata.error = error_msg
                metadata.extraction_complete = False
                metadata.extraction_confidence = 0.0

        return metadata

    async def extract_batch(
        self, file_paths: list[str | Path], max_concurrent: int = 5
    ) -> list[FileMetadata]:
        """
        Extract metadata from multiple files concurrently.

        Args:
            file_paths: List of file paths
            max_concurrent: Maximum number of concurrent extractions

        Returns:
            List of file metadata objects
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _extract_with_semaphore(file_path: str | Path) -> FileMetadata:
            async with semaphore:
                return await self.extract_metadata(file_path)

        tasks = [_extract_with_semaphore(path) for path in file_paths]
        return await asyncio.gather(*tasks)

    def _get_extractors_for_mime_type(
        self, mime_type: str
    ) -> list[BaseMetadataExtractor]:
        """
        Get all extractors that can handle the given MIME type.

        Args:
            mime_type: MIME type

        Returns:
            List of extractors for the MIME type
        """
        result = []

        # Check for exact MIME type match
        if mime_type in self.extractors:
            result.append(self.extractors[mime_type])

        # Check for MIME type prefix match (e.g., text/*)
        mime_prefix = mime_type.split("/")[0] + "/*"
        if (
            mime_prefix in self.extractors
            and self.extractors[mime_prefix] not in result
        ):
            result.append(self.extractors[mime_prefix])

        # Check for wildcard match
        if "*/*" in self.extractors and self.extractors["*/*"] not in result:
            result.append(self.extractors["*/*"])

        return result
