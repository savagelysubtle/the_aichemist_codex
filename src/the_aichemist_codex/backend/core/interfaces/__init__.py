"""
Interfaces for the AIchemist Codex core.

This package contains the interface definitions for the application.
"""

# Export interfaces
from .interfaces import (
    AnalyticsManager,
    AsyncIO,
    CacheProvider,
    ConfigProvider,
    ContentAnalyzer,
    DirectoryManager,
    FileManager,
    FileReader,
    FileTree,
    FileValidator,
    FileWriter,
    IndexManager,
    IngestManager,
    MetadataManager,
    NotificationManager,
    ProjectPaths,
    ProjectReader,
    RelationshipManager,
    SearchEngine,
    SearchProvider,
    TaggingManager,
    UserManager,
)

__all__ = [
    "AnalyticsManager",
    "AsyncIO",
    "CacheProvider",
    "ConfigProvider",
    "ContentAnalyzer",
    "DirectoryManager",
    "FileManager",
    "FileReader",
    "FileTree",
    "FileValidator",
    "FileWriter",
    "IndexManager",
    "IngestManager",
    "MetadataManager",
    "NotificationManager",
    "ProjectPaths",
    "ProjectReader",
    "RelationshipManager",
    "SearchEngine",
    "SearchProvider",
    "TaggingManager",
    "UserManager",
]
