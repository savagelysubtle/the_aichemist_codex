"""
Metadata extraction framework for The Aichemist Codex.

This module provides functionality for extracting rich metadata from various file types,
enabling intelligent content analysis, auto-tagging, and content categorization.
"""

from .extractor import BaseMetadataExtractor, MetadataExtractorRegistry

__all__ = ["BaseMetadataExtractor", "MetadataExtractorRegistry"]
