"""
Metadata extraction framework for The Aichemist Codex.

This module provides functionality for extracting rich metadata from various file types,
enabling intelligent content analysis, auto-tagging, and content categorization.
"""

from .audio_extractor import AudioMetadataExtractor
from .database_extractor import DatabaseMetadataExtractor
from .extractor import BaseMetadataExtractor, MetadataExtractorRegistry
from .image_extractor import ImageMetadataExtractor

__all__ = [
    "BaseMetadataExtractor",
    "MetadataExtractorRegistry",
    "ImageMetadataExtractor",
    "AudioMetadataExtractor",
    "DatabaseMetadataExtractor",
]
