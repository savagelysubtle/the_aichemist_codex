"""
File Metadata Module - Provides functionality for extracting and managing file metadata.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class FileMetadata:
    """Represents metadata for a file in the system."""

    # File identification
    path: Path
    name: str = field(default="")
    size: int = field(default=0)

    # Type information
    mime_type: str = field(default="")
    extension: str = field(default="")

    # Timestamps
    created_at: datetime | None = None
    modified_at: datetime | None = None
    accessed_at: datetime | None = None

    # Windows-specific attributes
    is_hidden: bool = field(default=False)
    is_system: bool = field(default=False)
    is_readonly: bool = field(default=False)

    # Content preview
    preview: str = field(default="")

    # Content analysis
    word_count: int = field(default=0)

    # Additional metadata (format-specific)
    additional: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Populate name and extension from path if needed."""
        if self.path and not self.name:
            self.name = self.path.name
            self.extension = self.path.suffix

    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "path": str(self.path),
            "name": self.name,
            "size": self.size,
            "mime_type": self.mime_type,
            "extension": self.extension,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
            "accessed_at": self.accessed_at.isoformat() if self.accessed_at else None,
            "is_hidden": self.is_hidden,
            "is_system": self.is_system,
            "is_readonly": self.is_readonly,
            "word_count": self.word_count,
            "additional": self.additional,
        }
