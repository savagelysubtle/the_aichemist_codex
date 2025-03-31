"""
Relationship models for domain layer.

This module defines core domain models for representing relationships
between entities in the system.
"""

from enum import Enum, auto
from pathlib import Path
from typing import Any


class RelationshipType(Enum):
    """Types of relationships between files."""

    # Reference relationships
    IMPORTS = auto()  # File imports/includes another file
    REFERENCES = auto()  # File references another file (e.g., mentions filename)
    LINKS_TO = auto()  # File contains a link to another file

    # Similarity relationships
    SIMILAR_TO = auto()  # Files have similar content
    RELATED_TO = auto()  # Files are related by topic/subject

    # Structural relationships
    PART_OF = auto()  # File is part of a larger unit (e.g., chapter in book)
    CONTAINS = auto()  # File contains another file (e.g., zip archive)

    # Temporal relationships
    PRECEDES = auto()  # File comes before another in a sequence
    FOLLOWS = auto()  # File comes after another in a sequence

    # Creation relationships
    GENERATED_FROM = auto()  # File was generated from another file
    DERIVED_FROM = auto()  # File was derived from another file


class Relationship:
    """
    Represents a relationship between two files or entities.

    This class defines the core attributes of a relationship between
    two entities in the system, including the relationship type,
    direction, and metadata.
    """

    def __init__(
        self,
        source: Path,
        target: Path,
        relationship_type: RelationshipType,
        bidirectional: bool = False,
        metadata: dict[str, Any] | None = None,
        strength: float = 1.0,
        id: str = "",
    ) -> None:
        """
        Initialize a relationship between two entities.

        Args:
            source: Source entity path
            target: Target entity path
            relationship_type: Type of relationship
            bidirectional: Whether the relationship applies in both directions
            metadata: Additional data about the relationship
            strength: Strength of the relationship (0.0 to 1.0)
            id: Optional relationship ID
        """
        self.source = source
        self.target = target
        self.relationship_type = relationship_type
        self.bidirectional = bidirectional
        self.metadata = metadata or {}
        self.strength = max(0.0, min(1.0, strength))  # Clamp between 0 and 1
        self.id = id

        # Compatibility attributes for graph.py
        self.source_path = source
        self.target_path = target
        self.rel_type = relationship_type

    def __eq__(self, other: object) -> bool:
        """Check if two relationships are equal."""
        if not isinstance(other, Relationship):
            return False

        # For bidirectional relationships, order doesn't matter
        if self.bidirectional and other.bidirectional:
            return (
                (self.source == other.source and self.target == other.target)
                or (self.source == other.target and self.target == other.source)
            ) and self.relationship_type == other.relationship_type

        # For directional relationships, order matters
        return (
            self.source == other.source
            and self.target == other.target
            and self.relationship_type == other.relationship_type
            and self.bidirectional == other.bidirectional
        )

    def __hash__(self) -> int:
        """Generate a hash for the relationship."""
        # For bidirectional relationships, order shouldn't affect the hash
        if self.bidirectional:
            paths = sorted([str(self.source), str(self.target)])
            return hash(
                (paths[0], paths[1], self.relationship_type, self.bidirectional)
            )

        # For directional relationships, order matters
        return hash(
            (
                str(self.source),
                str(self.target),
                self.relationship_type,
                self.bidirectional,
            )
        )

    def __repr__(self) -> str:
        """Return string representation of the relationship."""
        direction = "<->" if self.bidirectional else "->"
        return f"Relationship({self.source} {direction} {self.target} : {self.relationship_type.name})"

    def get_inverse(self) -> "Relationship":
        """
        Get the inverse of this relationship.

        Returns:
            A new relationship with source and target swapped
        """
        return Relationship(
            source=self.target,
            target=self.source,
            relationship_type=self.relationship_type,
            bidirectional=self.bidirectional,
            metadata=self.metadata.copy(),
            strength=self.strength,
            id=self.id,
        )
