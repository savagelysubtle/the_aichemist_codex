"""
Memory Entity

This module is part of the domain layer of the AIchemist Codex.
Location: src/the_aichemist_codex/domain/entities/memory.py

Defines the Memory entity representing a stored unit of information within the system.
Memory entities capture information that can be recalled based on contextual cues.

Dependencies:
- None (domain layer should not depend on outer layers)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from uuid import UUID, uuid4


class MemoryType(Enum):
    """Types of memories stored in the system."""

    DOCUMENT = auto()
    CONCEPT = auto()
    RELATION = auto()
    METADATA = auto()
    EVENT = auto()


@dataclass
class MemoryStrength:
    """Value object representing the strength of a memory."""

    initial_value: float
    current_value: float
    last_accessed: datetime
    access_count: int = 0

    def strengthen(self, amount: float = 0.1) -> None:
        """Increase the memory strength when accessed."""
        self.current_value = min(1.0, self.current_value + amount)
        self.access_count += 1
        self.last_accessed = datetime.now()

    def decay(self, factor: float = 0.05) -> None:
        """Decay the memory strength over time."""
        time_since_access = (datetime.now() - self.last_accessed).total_seconds()
        decay_amount = factor * (time_since_access / (3600 * 24))  # Daily decay
        self.current_value = max(0.1, self.current_value - decay_amount)


@dataclass
class Memory:
    """
    Represents a unit of information stored within the system that can be recalled.

    Memories can link to documents, concepts, or other types of information and
    include contextual data to help with recall and association.
    """

    content: str
    type: MemoryType
    id: UUID = field(default_factory=uuid4)
    source_id: UUID | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime | None = None
    tags: set[str] = field(default_factory=set)
    metadata: dict[str, str | int | float | bool | list] = field(default_factory=dict)
    strength: MemoryStrength = field(
        default_factory=lambda: MemoryStrength(
            initial_value=0.5,
            current_value=0.5,
            last_accessed=datetime.now(),
            access_count=1,
        )
    )

    def access(self) -> None:
        """Record access to this memory, strengthening it."""
        self.strength.strengthen()
        self.updated_at = datetime.now()

    def update_content(self, new_content: str) -> None:
        """Update the memory content."""
        self.content = new_content
        self.updated_at = datetime.now()
        self.access()

    def add_tag(self, tag: str) -> None:
        """Add a tag to the memory."""
        self.tags.add(tag)
        self.updated_at = datetime.now()

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the memory if it exists."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now()

    def add_metadata(self, key: str, value: str | int | float | bool | list) -> None:
        """Add metadata to the memory."""
        self.metadata[key] = value
        self.updated_at = datetime.now()

    def get_relevance_score(self, query: str, tags: set[str] | None = None) -> float:
        """
        Calculate a relevance score for this memory against a query.

        This is a simple implementation that could be enhanced with more
        sophisticated matching algorithms in the infrastructure layer.
        """
        # Basic relevance calculation based on content and tags
        content_match = 1.0 if query.lower() in self.content.lower() else 0.0

        tag_match = 0.0
        if tags:
            matching_tags = len(tags.intersection(self.tags))
            tag_match = matching_tags / len(tags) if len(tags) > 0 else 0.0

        # Combine content, tags, and memory strength
        relevance = (
            (content_match * 0.6)
            + (tag_match * 0.2)
            + (self.strength.current_value * 0.2)
        )
        return relevance
