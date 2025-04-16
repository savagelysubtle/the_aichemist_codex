"""
Recall Context Value Object

This module is part of the domain layer of the AIchemist Codex.
Location: src/the_aichemist_codex/domain/value_objects/recall_context.py

Defines the RecallContext value object that represents the context for memory recall.
This immutable object encapsulates the parameters that influence memory recall.

Dependencies:
- None (domain layer should not depend on outer layers)
"""

from dataclasses import dataclass, field
from enum import Enum, auto


class RecallStrategy(Enum):
    """Strategies for recalling memories."""

    MOST_RECENT = auto()  # Prioritize recently created/accessed memories
    STRONGEST = auto()  # Prioritize memories with highest strength
    MOST_RELEVANT = auto()  # Prioritize memories with highest content relevance
    ASSOCIATIVE = auto()  # Prioritize memories with strongest associations
    COMPREHENSIVE = auto()  # Balanced approach using all factors


@dataclass(frozen=True)
class RecallContext:
    """
    Immutable value object representing the context for memory recall.

    This object encapsulates all the parameters that influence how memories
    are recalled, including the query, filters, and recall strategy.
    """

    query: str
    strategy: RecallStrategy = RecallStrategy.MOST_RELEVANT
    tags: frozenset[str] = field(default_factory=frozenset)
    memory_types: frozenset[str] | None = None
    max_results: int = 10
    min_relevance: float = 0.2
    include_metadata: bool = True
    prioritize_recency: bool = True
    prioritize_strength: bool = True

    def __post_init__(self: "RecallContext") -> None:
        """Validate the recall context after initialization."""
        if self.max_results <= 0:
            object.__setattr__(self, "max_results", 10)

        if self.min_relevance < 0 or self.min_relevance > 1:
            object.__setattr__(self, "min_relevance", 0.2)

    def with_tags(self: "RecallContext", tags: set[str]) -> "RecallContext":
        """Create a new instance with additional tags."""
        combined_tags = frozenset(set(self.tags).union(tags))
        return RecallContext(
            query=self.query,
            strategy=self.strategy,
            tags=combined_tags,
            memory_types=self.memory_types,
            max_results=self.max_results,
            min_relevance=self.min_relevance,
            include_metadata=self.include_metadata,
            prioritize_recency=self.prioritize_recency,
            prioritize_strength=self.prioritize_strength,
        )

    def with_strategy(
        self: "RecallContext", strategy: RecallStrategy
    ) -> "RecallContext":
        """Create a new instance with a different strategy."""
        return RecallContext(
            query=self.query,
            strategy=strategy,
            tags=self.tags,
            memory_types=self.memory_types,
            max_results=self.max_results,
            min_relevance=self.min_relevance,
            include_metadata=self.include_metadata,
            prioritize_recency=self.prioritize_recency,
            prioritize_strength=self.prioritize_strength,
        )

    def with_limit(self: "RecallContext", max_results: int) -> "RecallContext":
        """Create a new instance with a different result limit."""
        return RecallContext(
            query=self.query,
            strategy=self.strategy,
            tags=self.tags,
            memory_types=self.memory_types,
            max_results=max(1, max_results),  # Ensure at least 1 result
            min_relevance=self.min_relevance,
            include_metadata=self.include_metadata,
            prioritize_recency=self.prioritize_recency,
            prioritize_strength=self.prioritize_strength,
        )
