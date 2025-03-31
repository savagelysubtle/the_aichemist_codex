"""
Memory Events

This module is part of the domain layer of the AIchemist Codex.
Location: src/the_aichemist_codex/domain/events/memory_events.py

Defines domain events related to memory operations.
These events are raised when significant memory actions occur.

Dependencies:
- None (domain layer should not depend on outer layers)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class MemoryCreatedEvent:
    """Event raised when a new memory is created."""

    memory_id: UUID
    memory_type: str
    source_id: UUID | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    tags: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class MemoryAccessedEvent:
    """Event raised when a memory is accessed."""

    memory_id: UUID
    access_context: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class MemoryUpdatedEvent:
    """Event raised when a memory is updated."""

    memory_id: UUID
    updated_fields: list[str]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class MemoryAssociationCreatedEvent:
    """Event raised when a new association between memories is created."""

    association_id: UUID
    source_id: UUID
    target_id: UUID
    association_type: str
    bidirectional: bool = False
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class MemoryAssociationStrengthChangedEvent:
    """Event raised when a memory association's strength changes."""

    association_id: UUID
    old_strength: float
    new_strength: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class MemoriesRecalledEvent:
    """Event raised when memories are recalled through a query."""

    query: str
    memory_ids: list[UUID]
    result_count: int
    recall_context: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class MemoryMergedEvent:
    """Event raised when memories are merged."""

    source_memory_ids: list[UUID]
    result_memory_id: UUID
    timestamp: datetime = field(default_factory=datetime.now)
