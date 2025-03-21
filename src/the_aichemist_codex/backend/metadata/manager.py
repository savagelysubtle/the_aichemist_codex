"""Metadata extraction manager.

This module provides a central manager for coordinating metadata extraction
across different file types using appropriate extractors.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any, cast

from the_aichemist_codex.backend.file_reader.file_metadata import FileMetadata
from the_aichemist_codex.backend.utils.cache.cache_manager import CacheManager
from the_aichemist_codex.backend.utils.io.mime_type_detector import MimeTypeDetector

from .extractor import BaseMetadataExtractor, MetadataExtractorRegistry

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
            extractor_name = extractor_class.__name__
            self.extractors[extractor_name] = extractor

        logger.info(f"Initialized {len(self.extractors)} metadata extractors")

    async def extract_metadata(
        self,
        file_path: str | Path,
        content: str | None = None,
        mime_type: str | None = None,
        metadata: FileMetadata | None = None,
    ) -> FileMetadata:
        """Extract metadata from a file.

        Args:
            file_path: Path to the file
            content: Optional pre-loaded file content
            mime_type: Optional MIME type of the file
            metadata: Optional existing metadata to enhance

        Returns:
            FileMetadata object with extracted metadata
        """
        start_time = time.time()

        # Convert file_path to Path object
        if isinstance(file_path, str):
            file_path = Path(file_path)

        # Ensure the file exists
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return FileMetadata(
                path=file_path,  # Use Path object directly
                mime_type="",  # Empty string as default
                size=0,
                extension="",
                preview="",
                error="File not found",
                extraction_complete=False,
            )

        # Create a new metadata object if one was not provided
        if metadata is None:
            metadata = FileMetadata(
                path=file_path,  # Use Path object directly
                mime_type="",  # Will be updated below
                size=0,  # Will be updated below
                extension="",  # Will be updated below
                preview="",  # Default empty preview
            )

        # Detect MIME type if not provided
        detected_mime_type = ""
        if mime_type is None:
            try:
                # The get_mime_type method returns a tuple (mime_type, confidence)
                mime_type_result = self.mime_detector.get_mime_type(file_path)
                detected_mime_type = mime_type_result[0] or "application/octet-stream"
            except Exception as e:
                logger.error(f"Error detecting MIME type: {e}")
                detected_mime_type = "application/octet-stream"  # Default MIME type

            # Use the detected mime type
            mime_type = detected_mime_type

        # Assign mime_type with proper null check
        if mime_type is not None:
            metadata.mime_type = mime_type
        else:
            metadata.mime_type = "application/octet-stream"  # Default MIME type

        # Set basic file attributes
        metadata.size = file_path.stat().st_size
        metadata.extension = file_path.suffix.lower().lstrip(".")

        # Get appropriate extractors for this file type
        extractors = self._get_extractors_for_mime_type(metadata.mime_type)

        if not extractors:
            logger.warning(
                f"No suitable metadata extractors found for {metadata.mime_type}"
            )
            metadata.extraction_complete = False
            metadata.extraction_confidence = 0.0
            return metadata

        # Extract metadata using all applicable extractors
        try:
            # Run extractors in parallel
            extraction_tasks = []
            for extractor in extractors:
                extraction_tasks.append(
                    extractor.extract(file_path, content, metadata.mime_type, metadata)
                )

            # Await all extraction results
            extraction_results = await asyncio.gather(
                *extraction_tasks, return_exceptions=True
            )

            # Process results
            combined_metadata: dict[str, Any] = {}
            extraction_count = 0
            confidence_sum = 0.0

            for result in extraction_results:
                # Skip exceptions in the results
                if isinstance(result, Exception):
                    logger.error(f"Extraction error: {result}")
                    continue

                # Process only dictionary results, cast to ensure type checking
                result_dict = cast(dict[str, Any], result)

                # Merge this extractor's result into the combined metadata
                if result_dict.get("extraction_complete", False):
                    extraction_count += 1
                    confidence_sum += result_dict.get("extraction_confidence", 0.0)

                    # Update with all extracted fields
                    for key, value in result_dict.items():
                        if key not in [
                            "error",
                            "extraction_complete",
                            "extraction_confidence",
                            "extraction_time",
                        ]:
                            # Merge lists
                            if (
                                isinstance(value, list)
                                and key in combined_metadata
                                and isinstance(combined_metadata[key], list)
                            ):
                                combined_metadata[key] = list(
                                    set(combined_metadata[key] + value)
                                )
                            # Merge dictionaries
                            elif (
                                isinstance(value, dict)
                                and key in combined_metadata
                                and isinstance(combined_metadata[key], dict)
                            ):
                                combined_metadata[key].update(value)
                            # Otherwise just overwrite
                            else:
                                combined_metadata[key] = value

            # Calculate average confidence
            avg_confidence = (
                confidence_sum / extraction_count if extraction_count > 0 else 0.0
            )

            # Update metadata object with extracted data
            for key, value in combined_metadata.items():
                if hasattr(metadata, key):
                    setattr(metadata, key, value)

            # Set extraction metadata
            metadata.extraction_complete = extraction_count > 0
            metadata.extraction_confidence = avg_confidence
            metadata.extraction_time = time.time() - start_time

            return metadata

        except Exception as e:
            logger.error(f"Error extracting metadata for {file_path}: {e}")
            metadata.error = str(e)
            metadata.extraction_complete = False
            metadata.extraction_confidence = 0.0
            return metadata

    async def extract_batch(
        self, file_paths: list[str | Path], max_concurrent: int = 5
    ) -> list[FileMetadata]:
        """Extract metadata from multiple files in parallel.

        Args:
            file_paths: List of paths to files
            max_concurrent: Maximum number of concurrent extractions

        Returns:
            List of FileMetadata objects with extracted metadata
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
        """Get appropriate extractors for a given MIME type.

        Args:
            mime_type: MIME type of the file

        Returns:
            List of extractors capable of processing this file type
        """
        extractors = []

        # Try to get a specific extractor
        extractor_class = MetadataExtractorRegistry.get_extractor_for_mime_type(
            mime_type
        )
        if extractor_class:
            extractor_name = extractor_class.__name__
            if extractor_name in self.extractors:
                extractors.append(self.extractors[extractor_name])

        # If no specific extractor was found, try with more generic extractors
        if not extractors:
            # Extract main type (e.g., "text" from "text/plain")
            main_type = mime_type.split("/")[0] + "/*"

            extractor_class = MetadataExtractorRegistry.get_extractor_for_mime_type(
                main_type
            )
            if extractor_class:
                extractor_name = extractor_class.__name__
                if extractor_name in self.extractors:
                    extractors.append(self.extractors[extractor_name])

        return extractors
