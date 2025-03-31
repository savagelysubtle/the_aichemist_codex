"""
Memory Association Entity

This module is part of the domain layer of the AIchemist Codex.
Location: src/the_aichemist_codex/domain/entities/memory_association.py

Defines the MemoryAssociation entity representing connections between memories.
These associations enable semantic networks and relationship tracking.

Dependencies:
- None (domain layer should not depend on outer layers)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any
from uuid import UUID, uuid4


class AssociationType(Enum):
    """Types of associations between memories."""

    REFERENCE = auto()  # Direct reference/mention
    SIMILARITY = auto()  # Similar content/topics
    CAUSALITY = auto()  # Cause-effect relationship
    SEQUENCE = auto()  # Temporal sequence
    CONTAINMENT = auto()  # One contains the other
    CONTRAST = auto()  # Contrasting or opposing
    GENERALIZATION = auto()  # General to specific
    CUSTOM = auto()  # Custom relationship type


@dataclass
class MemoryAssociation:
    """
    Represents a connection between two memories.

    Associations form the basis of the memory graph, enabling navigation
    between related concepts and information retrieval through association chains.
    """

    source_id: UUID
    target_id: UUID
    association_type: AssociationType
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime | None = None
    strength: float = 0.5  # Initial association strength
    bidirectional: bool = False  # Whether the association applies in both directions
    context: str | None = None  # Contextual information about the association
    metadata: dict[str, Any] = field(default_factory=dict)

    def strengthen(self, amount: float = 0.1) -> None:
        """Strengthen the association when reinforced."""
        self.strength = min(1.0, self.strength + amount)
        self.updated_at = datetime.now()

    def weaken(self, amount: float = 0.1) -> None:
        """Weaken the association."""
        self.strength = max(0.0, self.strength - amount)
        self.updated_at = datetime.now()

    def set_bidirectional(self, bidirectional: bool = True) -> None:
        """Set whether the association is bidirectional."""
        self.bidirectional = bidirectional
        self.updated_at = datetime.now()

    def update_context(self, context: str) -> None:
        """Update the contextual information about the association."""
        self.context = context
        self.updated_at = datetime.now()

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the association."""
        self.metadata[key] = value
        self.updated_at = datetime.now()

    def get_effective_strength(self, relative_importance: float = 1.0) -> float:
        """
        Calculate the effective strength considering the relative importance.

        Args:
            relative_importance: A factor modifying the strength based on context

        Returns:
            The effective strength, always between 0.0 and 1.0
        """
        return min(1.0, self.strength * relative_importance)
