"""
Relationship detection functionality.

This module provides classes and utilities for detecting relationships
between files using various strategies.
"""

import logging
import os
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, cast

from ....backend.core.models.models import RelationshipType
from ....backend.registry import Registry
from .relationship import Relationship

logger = logging.getLogger(__name__)


class DetectionStrategy(ABC):
    """
    Abstract base class for relationship detection strategies.

    Concrete strategies should implement the detect_relationships method
    to identify relationships for a given file.
    """

    def __init__(self):
        """Initialize the detection strategy."""
        # Get the registry instance
        self._registry = Registry.get_instance()
        self._file_reader = self._registry.async_io
        self._validator = self._registry.file_validator

    @abstractmethod
    async def detect_relationships(self, file_path: Path) -> list[Relationship]:
        """
        Detect relationships for a file.

        Args:
            file_path: Path to the file

        Returns:
            List of detected relationships

        Raises:
            Exception: If detection fails
        """
        pass


class VectorSimilarityStrategy(DetectionStrategy):
    """
    Strategy for detecting semantic similarity relationships using vector embeddings.

    This strategy compares file content using vector embeddings to identify
    semantic similarities between files.
    """

    def __init__(self, similarity_threshold: float = 0.75):
        """
        Initialize the vector similarity strategy.

        Args:
            similarity_threshold: Minimum similarity score (0.0-1.0) to consider as a relationship
        """
        super().__init__()
        self._similarity_threshold = similarity_threshold
        # Use type casting to bypass linter error
        self._vector_store = cast(Any, self._registry).vector_store

    async def detect_relationships(self, file_path: Path) -> list[Relationship]:
        """
        Detect semantic similarity relationships for a file.

        Args:
            file_path: Path to the file

        Returns:
            List of detected similarity relationships
        """
        relationships = []

        try:
            # Validate the file exists
            if not file_path.exists():
                logger.warning(
                    f"File not found for relationship detection: {file_path}"
                )
                return relationships

            # Get file content
            content = await self._file_reader.read_file(str(file_path))

            # Get similar files from vector store
            similar_files = await self._vector_store.find_similar(
                content,
                collection="files",
                exclude_paths=[str(file_path)],
                limit=10,
                min_score=self._similarity_threshold,
            )

            # Convert results to relationships
            for result in similar_files:
                similar_path = result.get("path")
                similarity_score = result.get("score", 0.0)

                if similar_path and similarity_score >= self._similarity_threshold:
                    rel = Relationship(
                        source_path=file_path,
                        target_path=Path(similar_path),
                        rel_type=RelationshipType.SEMANTIC_SIMILARITY,
                        strength=similarity_score,
                        metadata={
                            "similarity_score": similarity_score,
                            "detection_method": "vector_embeddings",
                        },
                    )
                    relationships.append(rel)
                    logger.debug(
                        f"Detected similarity relationship: {file_path} -> {similar_path} (score: {similarity_score:.2f})"
                    )

            return relationships
        except Exception as e:
            logger.error(f"Error detecting semantic similarities: {str(e)}")
            return relationships


class ReferenceDetectionStrategy(DetectionStrategy):
    """
    Strategy for detecting reference relationships using pattern matching.

    This strategy analyzes file content using regex patterns to identify
    references to other files.
    """

    def __init__(self):
        """Initialize the reference detection strategy."""
        super().__init__()
        # Patterns to detect file references for different file types
        self._patterns = {
            ".py": [
                r"(?:from|import)\s+([\w.]+)",  # Python imports
                r"(?:open|with open)\(['\"]([^'\"]+)['\"]",  # File open statements
            ],
            ".md": [
                r"(?:!\[.*?\]|\[.*?\])\(([^)]+)\)",  # Markdown links and images
                r"(?:include|require)\(['\"]([^'\"]+)['\"]",  # Include statements
            ],
            ".txt": [
                r"(?:include|require|reference):\s*([^\s,]+)",  # Text file references
            ],
            # Generic patterns that apply to all file types
            "*": [
                r"['\"]([^'\"]+\.(py|md|txt|json|yaml|yml))['\"]",  # Quoted file paths
            ],
        }

    def _get_patterns_for_type(self, file_suffix: str) -> list[str]:
        """
        Get patterns for a specific file type.

        Args:
            file_suffix: The file extension (e.g., ".py")

        Returns:
            List of regex patterns for that file type
        """
        # Get patterns specific to this file type and generic patterns
        specific_patterns = self._patterns.get(file_suffix, [])
        generic_patterns = self._patterns.get("*", [])
        return specific_patterns + generic_patterns

    async def detect_relationships(self, file_path: Path) -> list[Relationship]:
        """
        Detect reference relationships for a file.

        Args:
            file_path: Path to the file

        Returns:
            List of detected reference relationships
        """
        relationships = []

        try:
            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                return relationships

            # Get file extension
            suffix = file_path.suffix.lower()

            # Get patterns for the file type
            patterns = self._get_patterns_for_type(suffix)
            if not patterns:
                return relationships  # No patterns for this file type

            # Read file content - using read_file method from AsyncIO interface
            content = await self._file_reader.read_file(str(file_path))

            # Extract references
            references = set()
            for pattern in patterns:
                matches = re.findall(pattern, content)
                references.update(matches)

            # Convert references to relationships
            for ref in references:
                try:
                    # Handle relative imports in Python
                    if (
                        suffix == ".py"
                        and "." in ref
                        and "/" not in ref
                        and "\\" not in ref
                    ):
                        # Convert dotted imports to paths
                        ref_path = file_path.parent / Path(
                            ref.replace(".", "/") + ".py"
                        )
                    else:
                        # Handle relative paths
                        ref_path = (file_path.parent / ref).resolve()

                    # Only add if the referenced file exists
                    if ref_path.exists():
                        rel = Relationship(
                            source_path=file_path,
                            target_path=ref_path,
                            rel_type=RelationshipType.REFERENCES,
                            strength=1.0,
                            metadata={
                                "reference_type": "explicit",
                                "detection_method": "pattern_matching",
                            },
                        )
                        relationships.append(rel)
                except Exception as e:
                    logger.debug(f"Error processing reference {ref}: {str(e)}")

            return relationships
        except Exception as e:
            logger.error(f"Error detecting references for {file_path}: {str(e)}")
            return relationships


class RelationshipDetector:
    """
    Main detector class that orchestrates relationship detection.

    This class uses multiple detection strategies to identify various
    types of relationships between files.
    """

    def __init__(self):
        """Initialize the relationship detector with default strategies."""
        self._registry = Registry.get_instance()
        self._strategies = [
            VectorSimilarityStrategy(),
            ReferenceDetectionStrategy(),
            # Add more strategies as they become available
        ]

    async def detect_relationships(self, file_path: Path) -> list[Relationship]:
        """
        Detect all types of relationships for a file.

        Args:
            file_path: Path to the file

        Returns:
            List of all detected relationships
        """
        relationships = []

        for strategy in self._strategies:
            try:
                strategy_results = await strategy.detect_relationships(file_path)
                relationships.extend(strategy_results)
            except Exception as e:
                logger.error(f"Error in {strategy.__class__.__name__}: {e}")

        return relationships

    async def add_strategy(self, strategy: DetectionStrategy) -> None:
        """
        Add a new detection strategy.

        Args:
            strategy: The strategy to add
        """
        self._strategies.append(strategy)

    async def detect_relationships_in_directory(
        self,
        directory: Path,
        recursive: bool = True,
        file_types: set[str] | None = None,
    ) -> dict[str, list[Relationship]]:
        """
        Detect relationships for all files in a directory.

        Args:
            directory: The directory to scan
            recursive: Whether to scan subdirectories
            file_types: Set of file extensions to process (e.g., {'.py', '.md'})

        Returns:
            Dictionary mapping file paths to their relationships
        """
        results = {}

        # Validate directory
        if not directory.exists() or not directory.is_dir():
            logger.error(f"Invalid directory: {directory}")
            return results

        # Get file list
        file_list = []
        if recursive:
            for root, _, files in os.walk(directory):
                for file in files:
                    file_path = Path(root) / file
                    if file_types is None or file_path.suffix.lower() in file_types:
                        file_list.append(file_path)
        else:
            for item in directory.iterdir():
                if item.is_file() and (
                    file_types is None or item.suffix.lower() in file_types
                ):
                    file_list.append(item)

        # Process each file
        for file_path in file_list:
            try:
                relationships = await self.detect_relationships(file_path)
                if relationships:
                    results[str(file_path)] = relationships
            except Exception as e:
                logger.error(f"Error detecting relationships for {file_path}: {e}")

        return results
