# FILE: src/the_aichemist_codex/domain/repositories/interfaces/memory_repository.py
"""
Memory Repository Interface

This module is part of the domain layer of the AIchemist Codex.
Location: src/the_aichemist_codex/domain/repositories/interfaces/memory_repository.py

Defines the interface (protocol) that memory repository implementations must adhere to.
This ensures that the domain layer can interact with different storage mechanisms
without depending on their specific implementation details.

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
    """
    Protocol defining the contract for memory repositories.

    Implementations of this protocol handle the persistence and retrieval
    of Memory and MemoryAssociation entities.
    """

    async def initialize(self: "MemoryRepositoryInterface") -> None:
        """Initialize the repository (e.g., create tables)."""
        ...

    async def save_memory(self: "MemoryRepositoryInterface", memory: Memory) -> UUID:
        """
        Save a memory entity. Handles both creation and updates (upsert).

        Args:
            memory: The Memory entity to save.

        Returns:
            The UUID of the saved memory.
        """
        ...

    async def get_memory(
        self: "MemoryRepositoryInterface", memory_id: UUID
    ) -> Memory | None:
        """
        Retrieve a memory by its unique ID.

        Args:
            memory_id: The UUID of the memory to retrieve.

        Returns:
            The Memory entity if found, otherwise None.
        """
        ...

    async def delete_memory(self: "MemoryRepositoryInterface", memory_id: UUID) -> bool:
        """
        Delete a memory by its unique ID. Also handles related associations.

        Args:
            memory_id: The UUID of the memory to delete.

        Returns:
            True if the deletion was successful, False otherwise.
        """
        ...

    async def update_memory(self: "MemoryRepositoryInterface", memory: Memory) -> bool:
        """
        Update an existing memory entity.

        Note: Depending on implementation, save_memory might handle upserts.
              This provides an explicit update method.

        Args:
            memory: The Memory entity with updated fields.

        Returns:
            True if the update was successful, False otherwise.
        """
        # This can often be implemented by calling save_memory
        # For the protocol, we define the signature.
        await self.save_memory(memory)
        return True  # Placeholder return for protocol compliance

    async def save_association(
        self: "MemoryRepositoryInterface", association: MemoryAssociation
    ) -> UUID:
        """
        Save a memory association entity. Handles creation and updates (upsert).

        Args:
            association: The MemoryAssociation entity to save.

        Returns:
            The UUID of the saved association.
        """
        ...

    async def get_association(
        self: "MemoryRepositoryInterface", association_id: UUID
    ) -> MemoryAssociation | None:
        """
        Retrieve a memory association by its unique ID.

        Args:
            association_id: The UUID of the association to retrieve.

        Returns:
            The MemoryAssociation entity if found, otherwise None.
        """
        ...

    async def find_associations(
        self: "MemoryRepositoryInterface", memory_id: UUID, bidirectional: bool = True
    ) -> list[MemoryAssociation]:
        """
        Find all associations connected to a specific memory.

        Args:
            memory_id: The UUID of the memory to find associations for.
            bidirectional: If True, include associations where the memory is
                           the target and the association is marked bidirectional.
                           If False, only include associations where the memory
                           is the source.

        Returns:
            A list of MemoryAssociation entities connected to the memory.
        """
        ...

    async def recall_memories(
        self: "MemoryRepositoryInterface", context: RecallContext
    ) -> list[Memory]:
        """
        Recall memories based on a specific context.

        Args:
            context: The RecallContext object containing query, filters, and strategy.

        Returns:
            A list of Memory entities matching the recall criteria.
        """
        ...

    async def find_by_tags(
        self: "MemoryRepositoryInterface", tags: set[str], match_all: bool = False
    ) -> list[Memory]:
        """
        Find memories that contain specific tags.

        Args:
            tags: A set of tags to search for.
            match_all: If True, memories must contain *all* specified tags.
                       If False, memories must contain *at least one* of the tags.

        Returns:
            A list of Memory entities matching the tag criteria.
        """
        ...

    async def find_by_type(
        self: "MemoryRepositoryInterface", memory_type: MemoryType
    ) -> list[Memory]:
        """
        Find memories of a specific type.

        Args:
            memory_type: The MemoryType enum value to filter by.

        Returns:
            A list of Memory entities matching the specified type.
        """
        ...

    async def find_strongest_associations(
        self: "MemoryRepositoryInterface",
        memory_id: UUID,
        association_type: AssociationType | None = None,
        limit: int = 10,
    ) -> list[tuple[MemoryAssociation, Memory]]:
        """
        Find the strongest associations for a given memory, optionally filtered by type.

        Args:
            memory_id: The UUID of the source memory.
            association_type: Optional AssociationType to filter by.
            limit: The maximum number of associations to return.

        Returns:
            A list of tuples, each containing (MemoryAssociation, related_Memory),
            sorted by association strength in descending order.
        """
        ...
