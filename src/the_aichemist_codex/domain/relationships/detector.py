# FILE: src/the_aichemist_codex/domain/relationships/detector.py
"""
Defines interfaces and base classes for relationship detection strategies.
"""

import abc
from enum import Enum, auto
from pathlib import Path

from .relationship import Relationship  # Import the consolidated Relationship model


class DetectionStrategy(Enum):
    """Enumeration of strategies for detecting file relationships."""

    IMPORT_ANALYSIS = auto()
    TEXT_REFERENCE = auto()
    LINK_ANALYSIS = auto()
    CONTENT_SIMILARITY = auto()
    KEYWORD_ANALYSIS = auto()
    DIRECTORY_STRUCTURE = auto()
    MODIFICATION_HISTORY = auto()
    CREATION_PATTERNS = auto()
    COMPILATION_ANALYSIS = auto()
    ALL = auto()


class RelationshipDetectorBase(abc.ABC):
    """
    Abstract base class for relationship detectors.

    Defines the interface for detecting relationships between files.
    Implementations should focus on specific detection strategies.
    """

    @abc.abstractmethod
    async def detect(
        self, file_path: Path, context: dict | None = None
    ) -> list[Relationship]:
        """
        Detect relationships involving the given file.

        Args:
            file_path: Path to the file to analyze.
            context: Optional context dictionary which might include workspace root,
                     existing relationships, or other relevant info.

        Returns:
            List of detected Relationship objects originating from or targeting the file_path.
        """
        pass

    @property
    @abc.abstractmethod
    def strategy(self) -> DetectionStrategy:
        """Get the detection strategy used by this detector."""
        pass
