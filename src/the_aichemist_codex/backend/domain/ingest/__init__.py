"""
Ingest system package.

This package provides functionality for ingesting and processing content
from various sources.
"""

from .ingest_manager import IngestManagerImpl
from .models import (
    ContentType,
    IngestContent,
    IngestJob,
    IngestSource,
    IngestStatus,
    ProcessedContent,
)
from .processors import (
    BaseContentProcessor,
    CodeContentProcessor,
    MarkdownContentProcessor,
    TextContentProcessor,
)
from .sources import BaseIngestSource, FilesystemIngestSource, WebIngestSource

__all__ = [
    "ContentType",
    "IngestContent",
    "IngestJob",
    "IngestSource",
    "IngestStatus",
    "ProcessedContent",
    "IngestManagerImpl",
    "BaseIngestSource",
    "FilesystemIngestSource",
    "WebIngestSource",
    "BaseContentProcessor",
    "TextContentProcessor",
    "MarkdownContentProcessor",
    "CodeContentProcessor",
]
