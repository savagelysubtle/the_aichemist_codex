"""
Memory Association Utilities

This module provides utility functions for creating and managing memory associations.
"""

import logging
from uuid import UUID

from the_aichemist_codex.domain.entities.memory import Memory
from the_aichemist_codex.domain.entities.memory_association import (
    AssociationType,
    MemoryAssociation,
)
from the_aichemist_codex.infrastructure.repositories.sqlite_memory_repository import (
    SQLiteMemoryRepository,
)

logger = logging.getLogger(__name__)


async def create_bidirectional_association(
    repository: SQLiteMemoryRepository,
    source_id: UUID,
    target_id: UUID,
    association_type: AssociationType,
    strength: float = 0.5,
    metadata: dict | None = None,
) -> tuple[MemoryAssociation, MemoryAssociation]:
    """
    Create bidirectional associations between two memories.

    Args:
        repository: The memory repository
        source_id: ID of the source memory
        target_id: ID of the target memory
        association_type: Type of association
        strength: Initial strength of the association (0.0-1.0)
        metadata: Optional metadata for the association

    Returns:
        A tuple containing both created associations (source->target, target->source)
    """
    # Create source->target association
    forward_assoc = MemoryAssociation(
        source_id=source_id,
        target_id=target_id,
        association_type=association_type,
        strength=strength,
        metadata=metadata or {},
    )

    # Create target->source association (same type or inverse if applicable)
    backward_assoc = MemoryAssociation(
        source_id=target_id,
        target_id=source_id,
        association_type=association_type,
        strength=strength,
        metadata=metadata or {},
    )

    # Save associations
    await repository.save_association(forward_assoc)
    await repository.save_association(backward_assoc)

    return forward_assoc, backward_assoc


async def link_related_memories(
    repository: SQLiteMemoryRepository,
    memory: Memory,
    tags_to_match: set[str] | None = None,
    min_tag_overlap: int = 2,
    max_associations: int = 5,
    association_type: AssociationType = AssociationType.SIMILARITY,
    initial_strength: float = 0.6,
) -> list[MemoryAssociation]:
    """
    Automatically link a memory to other related memories based on tag overlap.

    Args:
        repository: The memory repository
        memory: The memory to link to others
        tags_to_match: Specific tags to match (if None, uses all tags from the memory)
        min_tag_overlap: Minimum number of overlapping tags required to create an association
        max_associations: Maximum number of associations to create
        association_type: Type of association to create
        initial_strength: Initial strength of the associations

    Returns:
        List of created associations
    """
    created_associations = []

    # If no specific tags provided, use all tags from the memory
    tags = tags_to_match or memory.tags

    # Skip if memory has no tags or tags_to_match is empty
    if not tags:
        logger.info("No tags available for memory association linking")
        return created_associations

    # Find memories with matching tags
    potential_matches = await repository.find_by_tags(tags)

    # Filter out the current memory
    potential_matches = [m for m in potential_matches if m.id != memory.id]

    # Calculate tag overlap and sort by most overlap first
    matches_with_overlap = []
    for potential_match in potential_matches:
        overlap = len(tags.intersection(potential_match.tags))
        if overlap >= min_tag_overlap:
            matches_with_overlap.append((potential_match, overlap))

    # Sort by overlap (highest first)
    matches_with_overlap.sort(key=lambda x: x[1], reverse=True)

    # Create associations with top matches
    for match, overlap in matches_with_overlap[:max_associations]:
        try:
            # Calculate strength based on overlap
            # More overlap = stronger association
            tag_factor = min(1.0, overlap / len(tags))
            strength = initial_strength * (0.5 + 0.5 * tag_factor)

            # Create bidirectional association
            assoc_forward, assoc_backward = await create_bidirectional_association(
                repository=repository,
                source_id=memory.id,
                target_id=match.id,
                association_type=association_type,
                strength=strength,
                metadata={"tag_overlap": overlap, "auto_generated": True},
            )

            created_associations.extend([assoc_forward, assoc_backward])

            logger.debug(
                f"Created association between {memory.id} and {match.id} "
                f"with strength {strength:.2f} based on {overlap} overlapping tags"
            )
        except Exception as e:
            logger.error(f"Error creating association: {str(e)}")

    return created_associations


async def strengthen_associations_on_recall(
    repository: SQLiteMemoryRepository,
    recalled_memories: list[Memory],
    strengthen_amount: float = 0.05,
    max_depth: int = 1,
) -> None:
    """
    Strengthen associations between recalled memories.

    When multiple memories are recalled together, their associations are strengthened
    to reflect that they are related in this context.

    Args:
        repository: The memory repository
        recalled_memories: List of memories that were recalled together
        strengthen_amount: Amount to strengthen associations by
        max_depth: Maximum association depth to strengthen
    """
    if len(recalled_memories) <= 1:
        return

    # Strengthen direct associations between recalled memories
    for i, memory1 in enumerate(recalled_memories):
        for memory2 in recalled_memories[i + 1 :]:
            # Find any existing associations between these two memories
            associations = await repository.find_associations(memory1.id)
            for assoc in associations:
                # Check if this association connects to another recalled memory
                if assoc.target_id == memory2.id or assoc.source_id == memory2.id:
                    # Strengthen the association
                    assoc.strength += strengthen_amount
                    if assoc.strength > 1.0:
                        assoc.strength = 1.0

                    # Update in repository
                    await repository.save_association(assoc)

                    logger.debug(
                        f"Strengthened association between {memory1.id} and {memory2.id} "
                        f"to {assoc.strength:.2f}"
                    )


async def find_knowledge_gap_recommendations(
    repository: SQLiteMemoryRepository,
    memory: Memory,
    min_strength: float = 0.3,
    max_recommendations: int = 5,
) -> list[dict]:
    """
    Find knowledge gaps related to a memory based on association patterns.

    Args:
        repository: The memory repository
        memory: The memory to find knowledge gaps for
        min_strength: Minimum association strength to consider
        max_recommendations: Maximum number of recommendations to return

    Returns:
        List of dictionaries with recommendation information
    """
    recommendations = []

    # Get all associations for this memory
    direct_associations = await repository.find_associations(memory.id)

    # Filter by minimum strength
    strong_associations = [a for a in direct_associations if a.strength >= min_strength]

    # Collect all directly connected memory IDs
    direct_memory_ids = {
        a.target_id if a.source_id == memory.id else a.source_id
        for a in strong_associations
    }

    # Get all these memories
    connected_memories = []
    for mem_id in direct_memory_ids:
        connected_memory = await repository.get_memory(mem_id)
        if connected_memory:
            connected_memories.append(connected_memory)

    # Find frequent tag patterns in connected memories
    tag_counts = {}
    for connected_memory in connected_memories:
        for tag in connected_memory.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    # Filter to tags not present in the original memory
    missing_tags = {
        tag: count
        for tag, count in tag_counts.items()
        if tag not in memory.tags and count > 1
    }

    # Create recommendations based on missing tags
    for tag, count in sorted(missing_tags.items(), key=lambda x: x[1], reverse=True)[
        :max_recommendations
    ]:
        # Find memories with this tag that aren't directly connected
        memories_with_tag = await repository.find_by_tags({tag})
        unconnected_memories = [
            m
            for m in memories_with_tag
            if m.id not in direct_memory_ids and m.id != memory.id
        ]

        if unconnected_memories:
            recommendations.append(
                {
                    "tag": tag,
                    "frequency": count,
                    "suggestion": f"Consider connecting with memory about '{unconnected_memories[0].content[:50]}...'",
                    "memory_id": str(unconnected_memories[0].id),
                    "confidence": count / len(connected_memories),
                }
            )

    return recommendations[:max_recommendations]
