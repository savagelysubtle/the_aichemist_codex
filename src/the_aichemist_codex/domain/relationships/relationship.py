# FILE: src/the_aichemist_codex/domain/relationships/relationship.py
"""Consolidated Relationship model for AIchemist Codex domain."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from .relationship_type import RelationshipType


@dataclass
class Relationship:
    """
    Represents a relationship between two file system paths (or entities).

    This class defines the core attributes of a relationship, including the
    relationship type, direction, strength, and metadata.
    """

    source_path: Path
    """Path to the source entity."""

    target_path: Path
    """Path to the target entity."""

    type: RelationshipType
    """Type of relationship (e.g., IMPORTS, EXTENDS, USES)."""

    strength: float = 1.0
    """Strength of the relationship (0.0 to 1.0)."""

    bidirectional: bool = False
    """Whether the relationship applies in both directions."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional data about the relationship."""

    id: UUID = field(default_factory=uuid4)
    """Unique identifier for the relationship instance."""

    created_at: datetime = field(default_factory=datetime.now)
    """Timestamp when the relationship was created."""

    updated_at: datetime | None = None
    """Timestamp when the relationship was last updated."""

    def __post_init__(self) -> None:
        """Validate relationship attributes."""
        # Ensure paths are Path objects
        if isinstance(self.source_path, str):
            self.source_path = Path(self.source_path)
        if isinstance(self.target_path, str):
            self.target_path = Path(self.target_path)

        # Ensure strength is within bounds
        self.strength = max(0.0, min(1.0, self.strength))

    def __eq__(self, other: object) -> bool:
        """Check if two relationships are equal."""
        if not isinstance(other, Relationship):
            return False

        # If IDs are present and match, they are the same instance
        if self.id and other.id and self.id == other.id:
            return True

        # Check essential equality based on paths, type, and bidirectionality
        # For bidirectional relationships, order doesn't matter
        if self.bidirectional and other.bidirectional:
            paths_match = (
                self.source_path == other.source_path
                and self.target_path == other.target_path
            ) or (
                self.source_path == other.target_path
                and self.target_path == other.source_path
            )
            return paths_match and self.type == other.type

        # For directional relationships, order matters
        return (
            self.source_path == other.source_path
            and self.target_path == other.target_path
            and self.type == other.type
            and self.bidirectional == other.bidirectional
        )

    def __hash__(self) -> int:
        """Generate a hash for the relationship."""
        # Use ID if available for efficient hashing in sets/dicts
        if self.id:
            return hash(self.id)

        # Fallback hash based on essential properties
        if self.bidirectional:
            paths = tuple(sorted([str(self.source_path), str(self.target_path)]))
            return hash((paths, self.type, self.bidirectional))

        return hash(
            (
                str(self.source_path),
                str(self.target_path),
                self.type,
                self.bidirectional,
            )
        )

    def __repr__(self) -> str:
        """Return string representation of the relationship."""
        direction = "<->" if self.bidirectional else "->"
        return f"Relationship(id={str(self.id)[:8]}, {self.source_path.name} {direction} {self.target_path.name} : {self.type.name})"

    def get_inverse(self) -> "Relationship":
        """
        Get the inverse of this relationship.

        Returns:
            A new relationship with source and target swapped, potentially different ID.
        """
        return Relationship(
            source_path=self.target_path,
            target_path=self.source_path,
            type=self.type,
            bidirectional=self.bidirectional,
            metadata=self.metadata.copy(),
            strength=self.strength,
            # Note: a new ID is generated for the inverse instance unless explicitly managed
        )

    def update(
        self, strength: float | None = None, metadata: dict[str, Any] | None = None
    ) -> None:
        """Update relationship properties."""
        if strength is not None:
            self.strength = max(0.0, min(1.0, strength))
        if metadata is not None:
            self.metadata.update(metadata)
        self.updated_at = datetime.now()
