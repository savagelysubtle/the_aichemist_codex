"""
Core relationship classes and types.

This module defines the fundamental relationship structure that
forms the basis of the file relationship mapping system.
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from ....core.models import RelationshipType


class Relationship:
    """
    Represents a relationship between two files.

    This class provides a rich representation of relationships between files,
    including type, strength, and metadata.
    """

    def __init__(
        self,
        source_path: Path,
        target_path: Path,
        rel_type: RelationshipType,
        strength: float = 1.0,
        metadata: dict[str, Any] | None = None,
        relationship_id: str | None = None,
        created_time: datetime | None = None,
        modified_time: datetime | None = None,
    ):
        """
        Initialize a new relationship.

        Args:
            source_path: Path to the source file
            target_path: Path to the target file
            rel_type: Type of relationship (from RelationshipType enum)
            strength: Strength of the relationship (0.0 to 1.0)
            metadata: Additional metadata for the relationship
            relationship_id: Unique ID for the relationship (generated if not provided)
            created_time: Creation timestamp (current time if not provided)
            modified_time: Last modified timestamp (current time if not provided)
        """
        self.source_path = source_path
        self.target_path = target_path
        self.rel_type = rel_type
        self.strength = max(0.0, min(1.0, strength))  # Clamp to [0, 1]
        self.metadata = metadata or {}
        self.id = relationship_id or str(uuid.uuid4())
        self.created_time = created_time or datetime.now()
        self.modified_time = modified_time or datetime.now()

    def update(
        self,
        rel_type: RelationshipType | None = None,
        strength: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Update the relationship properties.

        Args:
            rel_type: New relationship type
            strength: New relationship strength
            metadata: New or updated metadata
        """
        if rel_type is not None:
            self.rel_type = rel_type

        if strength is not None:
            self.strength = max(0.0, min(1.0, strength))  # Clamp to [0, 1]

        if metadata is not None:
            # Update metadata, preserving existing keys
            self.metadata.update(metadata)

        # Update modification time
        self.modified_time = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the relationship to a dictionary.

        Returns:
            Dictionary representation of the relationship
        """
        return {
            "id": self.id,
            "source_path": str(self.source_path),
            "target_path": str(self.target_path),
            "rel_type": self.rel_type.name,
            "strength": self.strength,
            "created_time": self.created_time.isoformat(),
            "modified_time": self.modified_time.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Relationship":
        """
        Create a relationship from a dictionary.

        Args:
            data: Dictionary containing relationship data

        Returns:
            A new Relationship instance
        """
        return cls(
            source_path=Path(data["source_path"]),
            target_path=Path(data["target_path"]),
            rel_type=RelationshipType[data["rel_type"]],
            strength=data["strength"],
            metadata=data.get("metadata", {}),
            relationship_id=data.get("id"),
            created_time=datetime.fromisoformat(data["created_time"])
            if "created_time" in data
            else None,
            modified_time=datetime.fromisoformat(data["modified_time"])
            if "modified_time" in data
            else None,
        )
