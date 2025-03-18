"""
Version module for the rollback system.

This module provides structures for managing file versions and version metadata.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Version:
    """Represents a versioned file with metadata."""

    id: str
    original_path: Path
    version_path: Path
    version_name: str
    timestamp: datetime
    size: int
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Version":
        """Create a Version instance from a dictionary."""
        return cls(
            id=data["id"],
            original_path=Path(data["original_path"]),
            version_path=Path(data["version_path"]),
            version_name=data["version_name"],
            timestamp=datetime.fromisoformat(data["timestamp"])
            if isinstance(data["timestamp"], str)
            else data["timestamp"],
            size=data["size"],
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert the Version to a dictionary for serialization."""
        return {
            "id": self.id,
            "original_path": str(self.original_path),
            "version_path": str(self.version_path),
            "version_name": self.version_name,
            "timestamp": self.timestamp.isoformat(),
            "size": self.size,
            "metadata": self.metadata,
            "tags": self.tags,
        }

    def add_tag(self, tag: str) -> None:
        """Add a tag to the version."""
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> bool:
        """Remove a tag from the version."""
        if tag in self.tags:
            self.tags.remove(tag)
            return True
        return False
