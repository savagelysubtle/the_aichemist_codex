"""
Ingest data models.

This module defines data models for the ingest system, including ingest jobs,
sources, processors, and content.
"""

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


class IngestStatus(enum.Enum):
    """Status of an ingest job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class ContentType(enum.Enum):
    """Type of ingested content."""

    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    CODE = "code"
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    BINARY = "binary"
    UNKNOWN = "unknown"

    @classmethod
    def from_extension(cls, file_extension: str) -> "ContentType":
        """
        Determine content type from file extension.

        Args:
            file_extension: File extension (e.g., '.txt', '.md')

        Returns:
            ContentType based on extension
        """
        extension_map = {
            ".txt": ContentType.TEXT,
            ".md": ContentType.MARKDOWN,
            ".markdown": ContentType.MARKDOWN,
            ".html": ContentType.HTML,
            ".htm": ContentType.HTML,
            ".py": ContentType.CODE,
            ".js": ContentType.CODE,
            ".java": ContentType.CODE,
            ".cpp": ContentType.CODE,
            ".c": ContentType.CODE,
            ".cs": ContentType.CODE,
            ".go": ContentType.CODE,
            ".rs": ContentType.CODE,
            ".ts": ContentType.CODE,
            ".json": ContentType.JSON,
            ".xml": ContentType.XML,
            ".csv": ContentType.CSV,
        }

        ext = file_extension.lower()
        if not ext.startswith("."):
            ext = f".{ext}"

        return extension_map.get(ext, ContentType.UNKNOWN)


@dataclass
class IngestSource:
    """Configuration for an ingest source."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: str = ""  # e.g., "filesystem", "web", "database"
    config: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "config": self.config,
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IngestSource":
        """
        Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            IngestSource instance
        """
        source = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            type=data.get("type", ""),
            config=data.get("config", {}),
        )

        if "created_at" in data and data["created_at"]:
            source.created_at = datetime.fromisoformat(data["created_at"])

        if "last_used" in data and data["last_used"]:
            source.last_used = datetime.fromisoformat(data["last_used"])

        return source


@dataclass
class IngestContent:
    """Content ingested from a source."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""
    content_type: ContentType = ContentType.UNKNOWN
    path: str | None = None  # Original path or URL
    filename: str | None = None
    content: str | bytes = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    ingested_at: datetime = field(default_factory=datetime.now)

    @property
    def is_binary(self) -> bool:
        """Check if content is binary."""
        return (
            isinstance(self.content, bytes) or self.content_type == ContentType.BINARY
        )

    @property
    def text_content(self) -> str:
        """
        Get content as text.

        Returns:
            Text content

        Raises:
            TypeError: If content is binary
        """
        if self.is_binary:
            raise TypeError("Content is binary and cannot be converted to text")
        return str(self.content)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary.

        Note: Binary content is not included in the output.

        Returns:
            Dictionary representation
        """
        result = {
            "id": self.id,
            "source_id": self.source_id,
            "content_type": self.content_type.value,
            "path": self.path,
            "filename": self.filename,
            "metadata": self.metadata,
            "ingested_at": self.ingested_at.isoformat(),
        }

        # Only include content if it's text
        if not self.is_binary:
            result["content"] = self.content

        return result


@dataclass
class ProcessedContent:
    """Content after processing."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    ingest_content_id: str = ""
    content_type: ContentType = ContentType.UNKNOWN
    content: str | dict[str, Any] = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    processor_id: str = ""
    processed_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "ingest_content_id": self.ingest_content_id,
            "content_type": self.content_type.value,
            "content": self.content,
            "metadata": self.metadata,
            "processor_id": self.processor_id,
            "processed_at": self.processed_at.isoformat(),
        }


@dataclass
class IngestJob:
    """An ingest job."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    source_ids: list[str] = field(default_factory=list)
    processor_ids: list[str] = field(default_factory=list)
    status: IngestStatus = IngestStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    config: dict[str, Any] = field(default_factory=dict)
    ingest_content_ids: list[str] = field(default_factory=list)
    processed_content_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "name": self.name,
            "source_ids": self.source_ids,
            "processor_ids": self.processor_ids,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "error_message": self.error_message,
            "config": self.config,
            "ingest_content_ids": self.ingest_content_ids,
            "processed_content_ids": self.processed_content_ids,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IngestJob":
        """
        Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            IngestJob instance
        """
        job = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            source_ids=data.get("source_ids", []),
            processor_ids=data.get("processor_ids", []),
            status=IngestStatus(data.get("status", "pending")),
            config=data.get("config", {}),
            ingest_content_ids=data.get("ingest_content_ids", []),
            processed_content_ids=data.get("processed_content_ids", []),
        )

        if "created_at" in data and data["created_at"]:
            job.created_at = datetime.fromisoformat(data["created_at"])

        if "started_at" in data and data["started_at"]:
            job.started_at = datetime.fromisoformat(data["started_at"])

        if "completed_at" in data and data["completed_at"]:
            job.completed_at = datetime.fromisoformat(data["completed_at"])

        job.error_message = data.get("error_message")

        return job
