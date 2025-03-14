"""Document metadata extractor for extracting information from document files.

This module provides functionality for analyzing document content to extract
metadata such as authors, titles, creation dates, revisions, and other
document-specific attributes.
"""

import logging
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from backend.file_reader.file_metadata import FileMetadata
from backend.utils.cache_manager import CacheManager

from .extractor import BaseMetadataExtractor, MetadataExtractorRegistry

logger = logging.getLogger(__name__)


@MetadataExtractorRegistry.register
class DocumentMetadataExtractor(BaseMetadataExtractor):
    """Metadata extractor for document files.

    Analyzes document content to extract author information, titles, creation dates,
    page counts, and other document-specific metadata.
    """

    def __init__(self, cache_manager: Optional[CacheManager] = None):
        """Initialize the document metadata extractor.

        Args:
            cache_manager: Optional cache manager for caching extraction results
        """
        super().__init__(cache_manager)

        # Common patterns for extracting document metadata
        self.author_patterns = [
            r"Author:?\s*([^,\r\n]+)",
            r"by\s+([^,\r\n]+)",
            r"created\s+by\s+([^,\r\n]+)",
        ]

        self.title_patterns = [
            r"Title:?\s*([^\r\n]+)",
            r"Subject:?\s*([^\r\n]+)",
            r"Document\s+Name:?\s*([^\r\n]+)",
        ]

        self.date_patterns = [
            r"Date:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"Created:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"Modified:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"(\d{1,2}\s+\w+\s+\d{2,4})",  # 15 January 2023 format
        ]

        self.version_patterns = [
            r"Version:?\s*([\d.]+)",
            r"Rev(?:ision)?:?\s*([\d.]+)",
            r"v([\d.]+)",
        ]

    @property
    def supported_mime_types(self) -> List[str]:
        """List of MIME types supported by this extractor."""
        return [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "application/epub+zip",
            "application/rtf",
            "text/markdown",
            "text/plain",
            "application/x-latex",
        ]

    async def extract(
        self,
        file_path: Union[str, Path],
        content: Optional[str] = None,
        mime_type: Optional[str] = None,
        metadata: Optional[FileMetadata] = None,
    ) -> Dict[str, Any]:
        """Extract metadata from a document file.

        Args:
            file_path: Path to the file
            content: Optional pre-loaded file content
            mime_type: Optional MIME type of the file
            metadata: Optional existing metadata to enhance

        Returns:
            A dictionary containing extracted metadata
        """
        start_time = time.time()

        # Check if we have cached results
        if self.cache_manager:
            cache_key = f"document_metadata:{file_path}"
            cached_result = self.cache_manager.get(cache_key)
            if cached_result:
                logger.debug(f"Using cached metadata for {file_path}")
                return cached_result

        # Convert file_path to Path object
        if isinstance(file_path, str):
            file_path = Path(file_path)

        # If this is a binary document format, use specialized extraction if available
        # For this implementation, we'll focus on text-based documents

        # Get the content if not provided
        if content is None:
            content = await self._get_content(file_path)
            if not content:
                return {
                    "error": "Failed to read file content",
                    "extraction_complete": False,
                    "extraction_confidence": 0.0,
                    "extraction_time": time.time() - start_time,
                }

        # Extract document metadata
        extracted_data = {}

        # Try to extract basic document metadata using regular expressions
        authors = self._extract_authors(content)
        extracted_data["authors"] = authors

        title = self._extract_title(content, file_path)
        extracted_data["title"] = title

        dates = self._extract_dates(content)
        extracted_data["creation_date"] = dates.get("creation", "")
        extracted_data["modification_date"] = dates.get("modification", "")

        version = self._extract_version(content)
        extracted_data["version"] = version

        # Extract document statistics
        stats = self._calculate_statistics(content)
        extracted_data["statistics"] = stats

        # Generate tags
        tags = self._generate_tags(authors, title, dates, version, stats, file_path)
        extracted_data["tags"] = tags

        # Mark extraction as complete
        extracted_data["extraction_complete"] = True
        extracted_data["extraction_confidence"] = (
            0.6  # Moderate confidence for text-based extraction
        )
        extracted_data["extraction_time"] = time.time() - start_time

        # Cache the results if we have a cache manager
        if self.cache_manager:
            self.cache_manager.set(cache_key, extracted_data, ttl=3600)  # 1 hour cache

        return extracted_data

    def _extract_authors(self, content: str) -> List[str]:
        """Extract author information from document content.

        Args:
            content: Document content

        Returns:
            A list of detected authors
        """
        authors = []
        for pattern in self.author_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            authors.extend([match.strip() for match in matches if match.strip()])

        # Remove duplicates and return
        return list(set(authors))

    def _extract_title(self, content: str, file_path: Path) -> str:
        """Extract title from document content.

        Args:
            content: Document content
            file_path: Path to the file (used as fallback)

        Returns:
            The extracted title or filename if no title found
        """
        # Try to find a title in the content
        for pattern in self.title_patterns:
            matches = re.search(pattern, content, re.IGNORECASE)
            if matches and matches.group(1).strip():
                return matches.group(1).strip()

        # For markdown files, try to extract the first heading
        if file_path.suffix.lower() in [".md", ".markdown"]:
            md_title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            if md_title_match:
                return md_title_match.group(1).strip()

        # If no title found, use the filename (without extension) as a fallback
        return file_path.stem

    def _extract_dates(self, content: str) -> Dict[str, str]:
        """Extract creation and modification dates from document content.

        Args:
            content: Document content

        Returns:
            A dictionary containing creation and modification dates
        """
        dates = {"creation": "", "modification": ""}

        # Extract all dates from the content
        found_dates = []
        for pattern in self.date_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            found_dates.extend([match.strip() for match in matches if match.strip()])

        # If dates were found, try to assign them
        if found_dates:
            # Use the first date that looks like a creation date
            creation_match = re.search(
                r"(created|date|published).*?(\d+[/-]\d+[/-]\d+|\d+\s+\w+\s+\d+)",
                content,
                re.IGNORECASE,
            )
            if creation_match:
                dates["creation"] = creation_match.group(2).strip()
            elif found_dates:
                # Use the first date found as the creation date
                dates["creation"] = found_dates[0]

            # Look for a modification date
            modification_match = re.search(
                r"(modified|updated|revised).*?(\d+[/-]\d+[/-]\d+|\d+\s+\w+\s+\d+)",
                content,
                re.IGNORECASE,
            )
            if modification_match:
                dates["modification"] = modification_match.group(2).strip()
            elif len(found_dates) > 1:
                # Use the last date found as the modification date (if different from creation)
                if found_dates[-1] != dates["creation"]:
                    dates["modification"] = found_dates[-1]

        return dates

    def _extract_version(self, content: str) -> str:
        """Extract version information from document content.

        Args:
            content: Document content

        Returns:
            The extracted version string or empty string if not found
        """
        for pattern in self.version_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return ""

    def _calculate_statistics(self, content: str) -> Dict[str, int]:
        """Calculate document statistics.

        Args:
            content: Document content

        Returns:
            A dictionary of document statistics
        """
        stats = {}

        # Word count
        words = re.findall(r"\b\w+\b", content)
        stats["word_count"] = len(words)

        # Page count estimate (assuming ~500 words per page)
        stats["estimated_page_count"] = max(1, len(words) // 500)

        # Character count
        stats["character_count"] = len(content)

        # Paragraph count (estimated by double newlines)
        paragraphs = re.split(r"\n\s*\n", content)
        stats["paragraph_count"] = len(paragraphs)

        # Section count (estimated by headings in markdown or similar docs)
        headings = re.findall(r"^#+\s+", content, re.MULTILINE)
        stats["section_count"] = len(headings) if headings else 0

        return stats

    def _generate_tags(
        self,
        authors: List[str],
        title: str,
        dates: Dict[str, str],
        version: str,
        stats: Dict[str, int],
        file_path: Path,
    ) -> List[str]:
        """Generate tags based on document metadata.

        Args:
            authors: List of detected authors
            title: Document title
            dates: Dictionary of detected dates
            version: Document version
            stats: Document statistics
            file_path: Path to the file

        Returns:
            A list of generated tags
        """
        tags = set()

        # Add document type tag
        doc_type = file_path.suffix.lower().lstrip(".")
        if doc_type:
            tags.add(f"doc-type:{doc_type}")

        # Add size tag based on word count
        word_count = stats.get("word_count", 0)
        if word_count < 500:
            tags.add("size:small")
        elif word_count < 2000:
            tags.add("size:medium")
        else:
            tags.add("size:large")

        # Add author tags
        for author in authors:
            # Only add short author names as tags
            if len(author) < 20:
                tags.add(f"author:{author.lower()}")

        # Add version tag if available
        if version:
            tags.add(f"version:{version}")

        # Add date-based tags
        creation_date = dates.get("creation", "")
        if creation_date:
            try:
                # Try to parse the date and extract the year
                year_match = re.search(r"20\d\d|19\d\d", creation_date)
                if year_match:
                    tags.add(f"year:{year_match.group(0)}")
            except:
                pass

        # Add title-based tags if title is not too long
        if title and len(title) < 50:
            # Extract key nouns from title (simplified approach)
            title_words = re.findall(r"\b[A-Z][a-z]{2,}\b", title)
            for word in title_words:
                if len(word) > 3:
                    tags.add(word.lower())

        return list(tags)
