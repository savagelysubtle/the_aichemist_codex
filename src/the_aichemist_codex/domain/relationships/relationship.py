"""Relationship model for AIchemist Codex.

This module provides the Relationship class which represents a relationship
between two files in a codebase.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class Relationship:
    """Represents a relationship between two files.

    A relationship captures the connection between a source file and a target file,
    along with the type of relationship, its strength, and optional metadata.
    """

    source_path: Path
    """Path to the source file."""

    target_path: Path
    """Path to the target file."""

    type: str
    """Type of relationship (e.g., imports, extends, uses)."""

    strength: float = 1.0
    """Strength of the relationship (0.0-1.0)."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional metadata about the relationship."""

    id: int | None = None
    """Database ID of the relationship."""

    created_at: datetime | None = None
    """Timestamp when the relationship was created."""

    def __post_init__(self) -> None:
        """Validate relationship attributes."""
        # Ensure paths are Path objects
        if isinstance(self.source_path, str):
            self.source_path = Path(self.source_path)

        if isinstance(self.target_path, str):
            self.target_path = Path(self.target_path)

        # Ensure strength is within bounds
        self.strength = max(0.0, min(1.0, self.strength))

        # Set creation time if not provided
        if self.created_at is None:
            self.created_at = datetime.now()

    @property
    def is_bidirectional(self) -> bool:
        """Check if relationship should be considered bidirectional.

        Returns:
            True if the relationship is bidirectional
        """
        return self.metadata.get("bidirectional", False)

    def to_dict(self) -> dict[str, Any]:
        """Convert relationship to a dictionary.

        Returns:
            Dictionary representation of the relationship
        """
        return {
            "id": self.id,
            "source_path": str(self.source_path),
            "target_path": str(self.target_path),
            "type": self.type,
            "strength": self.strength,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Relationship":
        """Create a relationship from a dictionary.

        Args:
            data: Dictionary with relationship data

        Returns:
            New Relationship instance
        """
        # Convert created_at from ISO format if it's a string
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        # Ensure paths are present and valid
        source_path = data.get("source_path")
        if source_path is None:
            raise ValueError("source_path cannot be None")

        target_path = data.get("target_path")
        if target_path is None:
            raise ValueError("target_path cannot be None")

        return cls(
            source_path=source_path,
            target_path=target_path,
            type=data.get("type", ""),
            strength=data.get("strength", 1.0),
            metadata=data.get("metadata", {}),
            id=data.get("id"),
            created_at=created_at,
        )
