"""Memory entity for the AIchemist Codex domain layer."""

from datetime import datetime
from uuid import UUID, uuid4

from ..value_objects.memory_strength import MemoryStrength
from ..value_objects.memory_type import MemoryType


class Memory:
    """Core memory entity representing a piece of information in the system."""

    def __init__(
        self,
        content: str,
        memory_type: MemoryType,
        tags: set[str] = None,
        source_id: UUID | None = None,
        initial_strength: float = 1.0,
    ) -> None:
        """
        Initialize a new Memory instance.

        Args:
            content: The actual content of the memory
            memory_type: Type classification of the memory
            tags: Set of tags associated with the memory
            source_id: Optional ID of the source memory
            initial_strength: Initial strength value (0.0 to 1.0)
        """
        self.id = uuid4()
        self.content = content
        self.type = memory_type
        self.source_id = source_id
        self.tags = tags or set()
        self.created_at = datetime.utcnow()
        self.updated_at = None
        self.metadata = {}
        self.strength = MemoryStrength(initial_strength)

    def update_content(self, new_content: str) -> None:
        """Update the memory content and mark as updated."""
        self.content = new_content
        self.updated_at = datetime.utcnow()

    def add_tag(self, tag: str) -> None:
        """Add a new tag to the memory."""
        self.tags.add(tag)
        self.updated_at = datetime.utcnow()

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the memory."""
        self.tags.discard(tag)
        self.updated_at = datetime.utcnow()

    def update_metadata(self, key: str, value: any) -> None:
        """Update a metadata value."""
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()

    def access(self) -> None:
        """Record an access to this memory, updating its strength."""
        self.strength.record_access()
        self.updated_at = datetime.utcnow()
