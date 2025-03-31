"""
Relationship storage functionality.

This module provides classes for storing and retrieving relationships
between entities in the system.
"""

import logging
from pathlib import Path

from .models import Relationship, RelationshipType

logger = logging.getLogger(__name__)


class RelationshipStore:
    """
    Storage for file relationships.

    This class provides functionality to store, retrieve, and query
    relationships between files and other entities.
    """

    def __init__(self) -> None:
        """Initialize an empty relationship store."""
        self._relationships: dict[str, Relationship] = {}
        self._next_id = 1

    def add_relationship(self, relationship: Relationship) -> str:
        """
        Add a relationship to the store.

        Args:
            relationship: The relationship to add

        Returns:
            The ID assigned to the relationship
        """
        rel_id = str(self._next_id)
        self._next_id += 1

        # Store the relationship with its ID
        self._relationships[rel_id] = relationship
        logger.debug(f"Added relationship {rel_id}: {relationship}")

        return rel_id

    def get_relationship(self, rel_id: str) -> Relationship | None:
        """
        Get a relationship by ID.

        Args:
            rel_id: The relationship ID

        Returns:
            The relationship, or None if not found
        """
        return self._relationships.get(rel_id)

    def get_all_relationships(
        self,
        rel_types: list[RelationshipType] | None = None,
        min_strength: float = 0.0,
    ) -> list[Relationship]:
        """
        Get all relationships in the store, optionally filtered.

        Args:
            rel_types: Optional filter for relationship types
            min_strength: Minimum relationship strength (0.0 to 1.0)

        Returns:
            List of relationships matching the filters
        """
        # Start with all relationships
        relationships = list(self._relationships.values())

        # Filter by type if specified
        if rel_types:
            relationships = [
                rel for rel in relationships if rel.relationship_type in rel_types
            ]

        # Filter by strength
        if min_strength > 0:
            relationships = [
                rel for rel in relationships if rel.strength >= min_strength
            ]

        return relationships

    def find_relationships_for_file(
        self,
        file_path: Path,
        rel_types: list[RelationshipType] | None = None,
        min_strength: float = 0.0,
        as_source: bool = True,
        as_target: bool = True,
    ) -> list[Relationship]:
        """
        Find relationships involving a specific file.

        Args:
            file_path: The file to find relationships for
            rel_types: Optional filter for relationship types
            min_strength: Minimum relationship strength (0.0 to 1.0)
            as_source: Whether to include relationships where file is the source
            as_target: Whether to include relationships where file is the target

        Returns:
            List of relationships involving the file
        """
        # Get all matching relationships
        all_relationships = self.get_all_relationships(rel_types, min_strength)

        # Filter by file involvement
        results = []
        for rel in all_relationships:
            if as_source and rel.source == file_path:
                results.append(rel)
            elif as_target and rel.target == file_path:
                results.append(rel)

        return results

    def remove_relationship(self, rel_id: str) -> bool:
        """
        Remove a relationship from the store.

        Args:
            rel_id: The relationship ID

        Returns:
            True if removed, False if not found
        """
        if rel_id in self._relationships:
            del self._relationships[rel_id]
            logger.debug(f"Removed relationship {rel_id}")
            return True
        return False

    def clear(self) -> None:
        """Remove all relationships from the store."""
        self._relationships.clear()
        logger.debug("Cleared all relationships from store")

    def count(self) -> int:
        """
        Get the number of relationships in the store.

        Returns:
            Count of relationships
        """
        return len(self._relationships)
