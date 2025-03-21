"""
Core relationship classes and types.

This module defines the fundamental relationship structures and types
that form the basis of the file relationship mapping system.
"""

import uuid
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any


class RelationshipType(Enum):
    """Enumeration of possible relationship types between files."""

    # Reference relationships
    IMPORTS = auto()  # File imports or includes another file
    REFERENCES = auto()  # File references another file (e.g., in comments, docs)
    LINKS_TO = auto()  # File contains a link to another file

    # Content relationships
    SIMILAR_CONTENT = auto()  # Files have similar textual content
    SHARED_KEYWORDS = auto()  # Files share significant keywords

    # Structural relationships
    PARENT_CHILD = auto()  # Directory contains file relationship
    SIBLING = auto()  # Files in same directory

    # Temporal relationships
    MODIFIED_TOGETHER = auto()  # Files frequently modified in same commit/session
    CREATED_TOGETHER = auto()  # Files created at similar times

    # Derived relationships
    COMPILED_FROM = auto()  # File is compiled/generated from another file
    EXTRACTED_FROM = auto()  # File was extracted from another file

    # Custom relationship
    CUSTOM = auto()  # User-defined relationship


class Relationship:
    """
    Represents a relationship between two files.

    Attributes:
        source_path (Path): Path to the source file
        target_path (Path): Path to the target file
        rel_type (RelationshipType): Type of relationship
        strength (float): Strength of relationship (0.0 to 1.0)
        metadata (Dict[str, Any]): Additional data about the relationship
        created_at (datetime): When the relationship was first detected
        updated_at (datetime): When the relationship was last updated
        id (str): Unique identifier for the relationship
    """

    def __init__(
        self,
        source_path: Path,
        target_path: Path,
        rel_type: RelationshipType,
        strength: float = 1.0,
        metadata: dict[str, Any] | None = None,
        created_at: datetime | None = None,
        id: str | None = None,
    ):
        """
        Initialize a new relationship between two files.

        Args:
            source_path: Path to the source file
            target_path: Path to the target file
            rel_type: Type of relationship
            strength: Strength of relationship (0.0 to 1.0)
            metadata: Additional data about the relationship
            created_at: When the relationship was first detected
            id: Unique identifier for the relationship

        Raises:
            ValueError: If strength is not between 0.0 and 1.0
        """
        if not 0.0 <= strength <= 1.0:
            raise ValueError("Relationship strength must be between 0.0 and 1.0")

        self.source_path = source_path
        self.target_path = target_path
        self.rel_type = rel_type
        self.strength = strength
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now()
        self.updated_at = self.created_at
        self.id = id or str(uuid.uuid4())

    def update(
        self,
        strength: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Update the relationship with new information.

        Args:
            strength: New strength value (if None, keeps current value)
            metadata: New metadata to merge with existing (if None, keeps current)

        Raises:
            ValueError: If strength is not between 0.0 and 1.0
        """
        if strength is not None:
            if not 0.0 <= strength <= 1.0:
                raise ValueError("Relationship strength must be between 0.0 and 1.0")
            self.strength = strength

        if metadata:
            self.metadata.update(metadata)

        self.updated_at = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the relationship to a dictionary representation.

        Returns:
            Dictionary containing all relationship data
        """
        return {
            "id": self.id,
            "source_path": str(self.source_path),
            "target_path": str(self.target_path),
            "rel_type": self.rel_type.name,
            "strength": self.strength,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Relationship":
        """
        Create a relationship from a dictionary representation.

        Args:
            data: Dictionary containing relationship data

        Returns:
            New Relationship instance
        """
        return cls(
            source_path=Path(data["source_path"]),
            target_path=Path(data["target_path"]),
            rel_type=RelationshipType[data["rel_type"]],
            strength=data["strength"],
            metadata=data["metadata"],
            created_at=datetime.fromisoformat(data["created_at"]),
            id=data["id"],
        )

    def __eq__(self, other: object) -> bool:
        """Check if two relationships are equal."""
        if not isinstance(other, Relationship):
            return False
        return (
            self.source_path == other.source_path
            and self.target_path == other.target_path
            and self.rel_type == other.rel_type
        )

    def __hash__(self) -> int:
        """Generate a hash for the relationship."""
        return hash((str(self.source_path), str(self.target_path), self.rel_type))

    def __repr__(self) -> str:
        """String representation of the relationship."""
        return (
            f"Relationship({self.source_path} → {self.target_path}, "
            f"type={self.rel_type.name}, strength={self.strength:.2f})"
        )
