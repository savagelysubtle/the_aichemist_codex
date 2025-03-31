"""
Memory Repository Interface

This module is part of the domain layer of the AIchemist Codex.
Location: src/the_aichemist_codex/domain/repositories/interfaces/memory_repository.py

Defines the interface for repositories that handle memory storage and retrieval.
This is a protocol that must be implemented by concrete repository classes.

Dependencies:
- domain.entities.memory
- domain.entities.memory_association
- domain.value_objects.recall_context
"""

from typing import Protocol
from uuid import UUID

from the_aichemist_codex.domain.entities.memory import Memory, MemoryType
from the_aichemist_codex.domain.entities.memory_association import (
    AssociationType,
    MemoryAssociation,
)
from the_aichemist_codex.domain.value_objects.recall_context import RecallContext


class MemoryRepositoryInterface(Protocol):
    """Interface for memory storage and retrieval operations."""

    async def save_memory(self, memory: Memory) -> UUID:
        """
        Save a memory to the repository.

        Args:
            memory: The memory to save

        Returns:
            The UUID of the saved memory
        """
        ...

    async def get_memory(self, memory_id: UUID) -> Memory | None:
        """
        Retrieve a memory by its ID.

        Args:
            memory_id: The UUID of the memory to retrieve

        Returns:
            The memory if found, None otherwise
        """
        ...

    async def delete_memory(self, memory_id: UUID) -> bool:
        """
        Delete a memory by its ID.

        Args:
            memory_id: The UUID of the memory to delete

        Returns:
            True if successful, False otherwise
        """
        ...

    async def update_memory(self, memory: Memory) -> bool:
        """
        Update an existing memory.

        Args:
            memory: The memory with updated fields

        Returns:
            True if successful, False otherwise
        """
        ...

    async def save_association(self, association: MemoryAssociation) -> UUID:
        """
        Save a memory association.

        Args:
            association: The association to save

        Returns:
            The UUID of the saved association
        """
        ...

    async def get_association(self, association_id: UUID) -> MemoryAssociation | None:
        """
        Retrieve an association by its ID.

        Args:
            association_id: The UUID of the association to retrieve

        Returns:
            The association if found, None otherwise
        """
        ...

    async def find_associations(
        self, memory_id: UUID, bidirectional: bool = True
    ) -> list[MemoryAssociation]:
        """
        Find all associations for a given memory.

        Args:
            memory_id: The UUID of the memory
            bidirectional: Whether to include associations where this memory is the target

        Returns:
            List of associations connected to the memory
        """
        ...

    async def recall_memories(self, context: RecallContext) -> list[Memory]:
        """
        Recall memories based on the provided context.

        Args:
            context: The recall context with query and filters

        Returns:
            List of memories matching the recall criteria
        """
        ...

    async def find_by_tags(
        self, tags: set[str], match_all: bool = False
    ) -> list[Memory]:
        """
        Find memories with the specified tags.

        Args:
            tags: Set of tags to match
            match_all: If True, all tags must match; if False, any tag can match

        Returns:
            List of memories with matching tags
        """
        ...

    async def find_by_type(self, memory_type: MemoryType) -> list[Memory]:
        """
        Find memories of a specific type.

        Args:
            memory_type: The type of memories to find

        Returns:
            List of memories of the specified type
        """
        ...

    async def find_strongest_associations(
        self,
        memory_id: UUID,
        association_type: AssociationType | None = None,
        limit: int = 10,
    ) -> list[tuple[MemoryAssociation, Memory]]:
        """
        Find the strongest associations for a memory.

        Args:
            memory_id: The UUID of the memory
            association_type: Optional type to filter by
            limit: Maximum number of results

        Returns:
            List of tuples containing (association, related_memory)
        """
        ...
