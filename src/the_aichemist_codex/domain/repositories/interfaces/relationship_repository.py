# FILE: src/the_aichemist_codex/domain/repositories/interfaces/relationship_repository.py
"""
Interface for Relationship Repository.

Defines the contract for storing, retrieving, and managing Relationship entities.
"""

from pathlib import Path
from typing import Protocol
from uuid import UUID

from the_aichemist_codex.domain.relationships.relationship import Relationship
from the_aichemist_codex.domain.relationships.relationship_type import RelationshipType


class RelationshipRepositoryInterface(Protocol):
    """Interface for managing the persistence of Relationship entities."""

    async def initialize(self) -> None:
        """Initialize the repository (e.g., create tables)."""
        ...

    async def save(self, relationship: Relationship) -> Relationship:
        """
        Save or update a relationship.

        If the relationship (based on source, target, type, direction) exists,
        it might be updated. Otherwise, it's created.

        Args:
            relationship: The Relationship object to save.

        Returns:
            The saved or updated Relationship object (potentially with a generated ID).
        """
        ...

    async def get_by_id(self, relationship_id: UUID) -> Relationship | None:
        """
        Retrieve a relationship by its unique ID.

        Args:
            relationship_id: The UUID of the relationship.

        Returns:
            The Relationship object if found, otherwise None.
        """
        ...

    async def find_by_endpoints(
        self,
        source_path: Path,
        target_path: Path,
        rel_type: RelationshipType | None = None,
    ) -> list[Relationship]:
        """
        Find relationships directly connecting the source and target paths.

        Args:
            source_path: The source path.
            target_path: The target path.
            rel_type: Optional relationship type to filter by.

        Returns:
            A list of matching Relationship objects.
        """
        ...

    async def find_outgoing(
        self, source_path: Path, rel_type: RelationshipType | None = None
    ) -> list[Relationship]:
        """
        Find all relationships originating from the source path.

        Args:
            source_path: The source path.
            rel_type: Optional relationship type to filter by.

        Returns:
            A list of matching Relationship objects.
        """
        ...

    async def find_incoming(
        self, target_path: Path, rel_type: RelationshipType | None = None
    ) -> list[Relationship]:
        """
        Find all relationships targeting the target path.

        Args:
            target_path: The target path.
            rel_type: Optional relationship type to filter by.

        Returns:
            A list of matching Relationship objects.
        """
        ...

    async def get_all(self) -> list[Relationship]:
        """Retrieve all relationships stored in the repository."""
        ...

    async def delete(self, relationship_id: UUID) -> bool:
        """
        Delete a relationship by its ID.

        Args:
            relationship_id: The UUID of the relationship to delete.

        Returns:
            True if the relationship was deleted, False otherwise.
        """
        ...

    async def delete_by_endpoints(
        self,
        source_path: Path,
        target_path: Path,
        rel_type: RelationshipType | None = None,
    ) -> int:
        """
        Delete relationships directly connecting the source and target paths.

        Args:
            source_path: The source path.
            target_path: The target path.
            rel_type: Optional relationship type to filter by. If None, deletes all types.

        Returns:
            The number of relationships deleted.
        """
        ...
