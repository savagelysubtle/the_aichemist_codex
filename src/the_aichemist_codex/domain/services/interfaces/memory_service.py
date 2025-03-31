"""
Memory Service Interface

This module is part of the domain layer of the AIchemist Codex.
Location: src/the_aichemist_codex/domain/services/interfaces/memory_service.py

Defines the interface for domain services that handle memory operations.
This is a protocol that must be implemented by concrete service classes.

Dependencies:
- domain.entities.memory
- domain.entities.memory_association
- domain.value_objects.recall_context
"""

from typing import Any, Protocol
from uuid import UUID

from the_aichemist_codex.domain.entities.memory import Memory, MemoryType
from the_aichemist_codex.domain.entities.memory_association import (
    AssociationType,
    MemoryAssociation,
)
from the_aichemist_codex.domain.value_objects.recall_context import RecallContext


class MemoryServiceInterface(Protocol):
    """Interface for domain services dealing with memory operations."""

    async def create_memory(
        self,
        content: str,
        memory_type: MemoryType,
        source_id: UUID | None = None,
        tags: set[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Memory:
        """
        Create a new memory.

        Args:
            content: The content of the memory
            memory_type: The type of memory
            source_id: Optional ID of the source entity
            tags: Optional set of tags
            metadata: Optional metadata dictionary

        Returns:
            The created memory
        """
        ...

    async def recall(self, context: RecallContext) -> list[Memory]:
        """
        Recall memories based on the provided context.

        Args:
            context: The recall context with query and filters

        Returns:
            List of memories matching the recall criteria
        """
        ...

    async def associate(
        self,
        source_id: UUID,
        target_id: UUID,
        association_type: AssociationType,
        bidirectional: bool = False,
        context: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryAssociation:
        """
        Create an association between two memories.

        Args:
            source_id: The UUID of the source memory
            target_id: The UUID of the target memory
            association_type: The type of association
            bidirectional: Whether the association is bidirectional
            context: Optional context information
            metadata: Optional metadata

        Returns:
            The created memory association
        """
        ...

    async def strengthen_memory(self, memory_id: UUID, amount: float = 0.1) -> bool:
        """
        Strengthen a memory by accessing it.

        Args:
            memory_id: The UUID of the memory to strengthen
            amount: The amount to strengthen by

        Returns:
            True if successful, False otherwise
        """
        ...

    async def strengthen_association(
        self, source_id: UUID, target_id: UUID, amount: float = 0.1
    ) -> bool:
        """
        Strengthen an association between memories.

        Args:
            source_id: The UUID of the source memory
            target_id: The UUID of the target memory
            amount: The amount to strengthen by

        Returns:
            True if successful, False otherwise
        """
        ...

    async def find_related_memories(
        self,
        memory_id: UUID,
        max_depth: int = 2,
        min_strength: float = 0.3,
        limit: int = 20,
    ) -> list[tuple[list[MemoryAssociation], Memory]]:
        """
        Find memories related to the given memory through associations.

        Args:
            memory_id: The UUID of the memory
            max_depth: Maximum association depth to traverse
            min_strength: Minimum association strength to consider
            limit: Maximum number of results

        Returns:
            List of tuples containing (association_path, related_memory)
        """
        ...

    async def create_from_source(
        self,
        source_content: str,
        source_id: UUID,
        source_type: str,
        max_memories: int = 10,
        min_length: int = 50,
    ) -> list[Memory]:
        """
        Create memories from a source content by extracting key information.

        Args:
            source_content: The content to extract memories from
            source_id: The UUID of the source
            source_type: The type of the source
            max_memories: Maximum number of memories to create
            min_length: Minimum content length for a memory

        Returns:
            List of created memories
        """
        ...

    async def merge_memories(
        self, memory_ids: list[UUID], new_content: str | None = None
    ) -> Memory | None:
        """
        Merge multiple memories into a single memory.

        Args:
            memory_ids: List of memory IDs to merge
            new_content: Optional content for the merged memory

        Returns:
            The merged memory if successful, None otherwise
        """
        ...
